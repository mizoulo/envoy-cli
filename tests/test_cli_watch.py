"""Tests for envoy.cli_watch."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envoy.cli_watch import watch_cli
from envoy.watch import WatchEvent


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("KEY=val\n")
    return f


def test_list_watched_empty(runner: CliRunner, tmp_path: Path) -> None:
    with patch("envoy.cli_watch.Config") as MockConfig:
        MockConfig.return_value.get.return_value = []
        result = runner.invoke(watch_cli, ["list"])
    assert result.exit_code == 0
    assert "No watch targets" in result.output


def test_list_watched_with_targets(runner: CliRunner) -> None:
    targets = [{"path": ".env", "project": "myapp", "env": "dev"}]
    with patch("envoy.cli_watch.Config") as MockConfig:
        MockConfig.return_value.get.return_value = targets
        result = runner.invoke(watch_cli, ["list"])
    assert result.exit_code == 0
    assert "myapp/dev" in result.output


def test_start_dry_run_no_push(runner: CliRunner, env_file: Path) -> None:
    mock_watcher = MagicMock()
    events: list = []

    def fake_on_change(cb):
        events.append(cb)

    def fake_run():
        ev = WatchEvent(env_file, "proj", "dev", None, "abc")
        for cb in events:
            cb(ev)
        raise KeyboardInterrupt

    mock_watcher.on_change.side_effect = fake_on_change
    mock_watcher.run.side_effect = fake_run

    with patch("envoy.cli_watch.EnvWatcher", return_value=mock_watcher):
        result = runner.invoke(
            watch_cli,
            ["start", str(env_file), "-p", "proj", "-e", "dev", "--dry-run"],
        )
    assert result.exit_code == 0
    assert "Dry-run" in result.output
    assert "Stopped" in result.output


def test_start_pushes_on_change(runner: CliRunner, env_file: Path, tmp_path: Path) -> None:
    mock_watcher = MagicMock()
    cbs: list = []

    mock_watcher.on_change.side_effect = lambda cb: cbs.append(cb)

    def fake_run():
        ev = WatchEvent(env_file, "proj", "dev", "old", "new")
        for cb in cbs:
            cb(ev)
        raise KeyboardInterrupt

    mock_watcher.run.side_effect = fake_run

    mock_result = MagicMock(success=True, message="ok")
    mock_engine = MagicMock()
    mock_engine.push_file.return_value = mock_result

    with patch("envoy.cli_watch.EnvWatcher", return_value=mock_watcher), \
         patch("envoy.cli_watch._make_engine", return_value=mock_engine):
        result = runner.invoke(
            watch_cli,
            ["start", str(env_file), "-p", "proj", "-e", "dev",
             "--vault-dir", str(tmp_path)],
        )
    assert result.exit_code == 0
    assert "Pushed" in result.output
    mock_engine.push_file.assert_called_once()
