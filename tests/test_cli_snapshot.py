"""Tests for snapshot CLI commands."""

import pytest
from click.testing import CliRunner

from envoy.cli_snapshot import snapshot_cli
from envoy.storage import LocalStorage
from envoy.vault import Vault
from envoy.snapshot import SnapshotManager


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_dir(tmp_path):
    return str(tmp_path / "vault")


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB=postgres\nSECRET=abc")
    return str(p)


def test_capture_command(runner, vault_dir, env_file):
    result = runner.invoke(
        snapshot_cli,
        ["capture", "myapp", "prod", env_file, "--password", "pass", "--vault-dir", vault_dir],
    )
    assert result.exit_code == 0, result.output
    assert "Snapshot captured" in result.output


def test_capture_with_label(runner, vault_dir, env_file):
    result = runner.invoke(
        snapshot_cli,
        ["capture", "myapp", "prod", env_file, "--label", "v1", "--password", "pass", "--vault-dir", vault_dir],
    )
    assert result.exit_code == 0
    assert "v1" in result.output


def test_restore_command(runner, tmp_path, vault_dir, env_file):
    # First capture
    runner.invoke(
        snapshot_cli,
        ["capture", "myapp", "prod", env_file, "--password", "pass", "--vault-dir", vault_dir],
    )
    storage = LocalStorage(vault_dir, password="pass")
    vault = Vault(storage)
    manager = SnapshotManager(vault, "myapp")
    keys = manager.list_snapshots("prod")
    assert keys, "Expected at least one snapshot"
    ts = int(keys[0].split("/")[-1])
    out_file = str(tmp_path / "restored.env")
    result = runner.invoke(
        snapshot_cli,
        ["restore", "myapp", "prod", str(ts), "--output", out_file, "--password", "pass", "--vault-dir", vault_dir],
    )
    assert result.exit_code == 0, result.output
    assert "Restored" in result.output
    assert open(out_file).read() == "DB=postgres\nSECRET=abc"


def test_list_command_empty(runner, vault_dir):
    result = runner.invoke(
        snapshot_cli,
        ["list", "myapp", "prod", "--password", "pass", "--vault-dir", vault_dir],
    )
    assert result.exit_code == 0
    assert "No snapshots found" in result.output


def test_list_command_shows_keys(runner, vault_dir, env_file):
    runner.invoke(
        snapshot_cli,
        ["capture", "myapp", "prod", env_file, "--password", "pass", "--vault-dir", vault_dir],
    )
    result = runner.invoke(
        snapshot_cli,
        ["list", "myapp", "prod", "--password", "pass", "--vault-dir", vault_dir],
    )
    assert result.exit_code == 0
    assert "myapp/prod/snapshots/" in result.output
