"""Tests for envoy.cli_backup."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_backup import backup_cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("KEY=value\n")
    return f


def test_create_outputs_archive_path(runner: CliRunner, env_file: Path, tmp_path: Path):
    backup_dir = str(tmp_path / "backups")
    result = runner.invoke(
        backup_cli,
        ["create", str(env_file), "--backup-dir", backup_dir],
    )
    assert result.exit_code == 0
    assert "Backup created" in result.output


def test_create_with_label(runner: CliRunner, env_file: Path, tmp_path: Path):
    backup_dir = str(tmp_path / "backups")
    result = runner.invoke(
        backup_cli,
        ["create", str(env_file), "--backup-dir", backup_dir, "--label", "prod"],
    )
    assert result.exit_code == 0
    assert "prod" in result.output


def test_list_empty(runner: CliRunner, tmp_path: Path):
    backup_dir = str(tmp_path / "backups")
    result = runner.invoke(backup_cli, ["list", "--backup-dir", backup_dir])
    assert result.exit_code == 0
    assert "No backups found" in result.output


def test_list_shows_archives(runner: CliRunner, env_file: Path, tmp_path: Path):
    backup_dir = str(tmp_path / "backups")
    runner.invoke(backup_cli, ["create", str(env_file), "--backup-dir", backup_dir])
    result = runner.invoke(backup_cli, ["list", "--backup-dir", backup_dir])
    assert result.exit_code == 0
    assert ".tar.gz" in result.output


def test_restore_round_trip(runner: CliRunner, env_file: Path, tmp_path: Path):
    backup_dir = str(tmp_path / "backups")
    runner.invoke(backup_cli, ["create", str(env_file), "--backup-dir", backup_dir])
    archives = sorted((tmp_path / "backups").glob("*.tar.gz"))
    assert archives
    restore_dir = str(tmp_path / "restored")
    result = runner.invoke(
        backup_cli,
        ["restore", str(archives[0]), "--target-dir", restore_dir, "--backup-dir", backup_dir],
    )
    assert result.exit_code == 0
    assert "Restored to" in result.output
    assert (tmp_path / "restored" / env_file.name).exists()


def test_restore_missing_archive_exits_nonzero(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        backup_cli,
        ["restore", str(tmp_path / "ghost.tar.gz"), "--backup-dir", str(tmp_path)],
    )
    assert result.exit_code != 0


def test_prune_removes_old(runner: CliRunner, env_file: Path, tmp_path: Path):
    backup_dir = str(tmp_path / "backups")
    for _ in range(4):
        runner.invoke(backup_cli, ["create", str(env_file), "--backup-dir", backup_dir])
    result = runner.invoke(backup_cli, ["prune", "--keep", "2", "--backup-dir", backup_dir])
    assert result.exit_code == 0
    assert "pruned" in result.output


def test_prune_noop_message(runner: CliRunner, env_file: Path, tmp_path: Path):
    backup_dir = str(tmp_path / "backups")
    runner.invoke(backup_cli, ["create", str(env_file), "--backup-dir", backup_dir])
    result = runner.invoke(backup_cli, ["prune", "--keep", "10", "--backup-dir", backup_dir])
    assert result.exit_code == 0
    assert "Nothing to prune" in result.output
