"""Tests for envoy.cli_export CLI commands."""
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_export import export_cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\n# comment\nSECRET=abc123\n")
    return p


def test_convert_shell_stdout(runner, env_file):
    result = runner.invoke(export_cli, ["convert", str(env_file), "--format", "shell"])
    assert result.exit_code == 0
    assert "export DB_HOST=localhost" in result.output
    assert "export DB_PORT=5432" in result.output


def test_convert_json_stdout(runner, env_file):
    result = runner.invoke(export_cli, ["convert", str(env_file), "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["DB_HOST"] == "localhost"


def test_convert_docker_stdout(runner, env_file):
    result = runner.invoke(export_cli, ["convert", str(env_file), "--format", "docker"])
    assert result.exit_code == 0
    assert "--env DB_HOST=localhost" in result.output


def test_convert_writes_output_file(runner, env_file, tmp_path):
    out = tmp_path / "out.json"
    result = runner.invoke(
        export_cli,
        ["convert", str(env_file), "--format", "json", "--output", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "DB_HOST" in data
    assert "Exported" in result.output


def test_convert_missing_file(runner, tmp_path):
    result = runner.invoke(export_cli, ["convert", str(tmp_path / "missing.env")])
    assert result.exit_code != 0


def test_summary_command(runner, env_file):
    result = runner.invoke(export_cli, ["summary", str(env_file)])
    assert result.exit_code == 0
    assert "Keys   : 3" in result.output
    assert "- DB_HOST" in result.output
    assert "- SECRET" in result.output
