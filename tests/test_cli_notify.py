"""Tests for envoy.cli_notify."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envoy.cli_notify import notify_cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def notify_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".envoy"
    d.mkdir()
    return d


def _ctx(notify_dir: Path):
    return {"config_dir": str(notify_dir.parent / ".envoy")}


def test_add_webhook_outputs_confirmation(runner: CliRunner, notify_dir: Path):
    result = runner.invoke(
        notify_cli,
        ["add-webhook", "http://example.com/hook"],
        obj={"config_dir": str(notify_dir)},
    )
    assert result.exit_code == 0
    assert "http://example.com/hook" in result.output


def test_add_webhook_persists(runner: CliRunner, notify_dir: Path):
    runner.invoke(
        notify_cli,
        ["add-webhook", "http://example.com/hook"],
        obj={"config_dir": str(notify_dir)},
    )
    data = json.loads((notify_dir / "notify.json").read_text())
    assert data["channels"][0]["channel"] == "webhook"


def test_add_email_outputs_confirmation(runner: CliRunner, notify_dir: Path):
    result = runner.invoke(
        notify_cli,
        ["add-email", "ops@example.com"],
        obj={"config_dir": str(notify_dir)},
    )
    assert result.exit_code == 0
    assert "ops@example.com" in result.output


def test_add_log_outputs_confirmation(runner: CliRunner, notify_dir: Path):
    result = runner.invoke(
        notify_cli,
        ["add-log"],
        obj={"config_dir": str(notify_dir)},
    )
    assert result.exit_code == 0
    assert "Log channel" in result.output


def test_list_empty(runner: CliRunner, notify_dir: Path):
    result = runner.invoke(
        notify_cli,
        ["list"],
        obj={"config_dir": str(notify_dir)},
    )
    assert result.exit_code == 0
    assert "No notification" in result.output


def test_list_shows_registered_channels(runner: CliRunner, notify_dir: Path):
    runner.invoke(notify_cli, ["add-log"], obj={"config_dir": str(notify_dir)})
    runner.invoke(notify_cli, ["add-webhook", "http://a.com"], obj={"config_dir": str(notify_dir)})
    result = runner.invoke(notify_cli, ["list"], obj={"config_dir": str(notify_dir)})
    assert "webhook" in result.output
    assert "log" in result.output


def test_test_command_log_channel(runner: CliRunner, notify_dir: Path):
    runner.invoke(notify_cli, ["add-log"], obj={"config_dir": str(notify_dir)})
    result = runner.invoke(
        notify_cli,
        ["test", "--action", "ping", "--message", "hello"],
        obj={"config_dir": str(notify_dir)},
    )
    assert result.exit_code == 0
    assert "OK" in result.output


def test_test_command_no_channels(runner: CliRunner, notify_dir: Path):
    result = runner.invoke(
        notify_cli,
        ["test"],
        obj={"config_dir": str(notify_dir)},
    )
    assert result.exit_code == 0
    assert "No channels" in result.output
