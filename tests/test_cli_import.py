"""Tests for envoy/cli_import.py."""
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_import import import_cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    return f


@pytest.fixture()
def json_file(tmp_path: Path) -> Path:
    f = tmp_path / "env.json"
    f.write_text(json.dumps({"API_KEY": "secret", "DEBUG": "true"}))
    return f


def test_preview_dotenv(runner: CliRunner, env_file: Path):
    result = runner.invoke(import_cli, ["preview", str(env_file)])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "DB_PORT" in result.output
    assert "Would import 2" in result.output


def test_preview_json(runner: CliRunner, json_file: Path):
    result = runner.invoke(import_cli, ["preview", str(json_file), "--format", "json"])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "DEBUG" in result.output


def test_preview_empty_file(runner: CliRunner, tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("# just a comment\n")
    result = runner.invoke(import_cli, ["preview", str(f)])
    assert result.exit_code == 0
    assert "No variables found" in result.output


def test_run_imports_into_vault(runner: CliRunner, env_file: Path, tmp_path: Path):
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    result = runner.invoke(
        import_cli,
        ["run", str(env_file), "--project", "myapp", "--env", "staging",
         "--password", "s3cr3t"],
        env={"ENVOY_VAULT_DIR": str(vault_dir)},
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Imported 2 key(s)" in result.output
    assert "myapp/staging" in result.output


def test_run_json_format(runner: CliRunner, json_file: Path, tmp_path: Path):
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    result = runner.invoke(
        import_cli,
        ["run", str(json_file), "--project", "svc", "--format", "json",
         "--password", "pass"],
        env={"ENVOY_VAULT_DIR": str(vault_dir)},
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Imported 2 key(s)" in result.output
