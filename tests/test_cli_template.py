"""Tests for envoy.cli_template CLI commands."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_template import template_cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def template_file(tmp_path: Path) -> Path:
    f = tmp_path / "template.env"
    f.write_text("DB={{ DB_HOST }}\nPORT={{ DB_PORT }}\n", encoding="utf-8")
    return f


def test_render_to_stdout(runner: CliRunner, template_file: Path):
    result = runner.invoke(template_cli, ["render", str(template_file), "-v", "DB_HOST=localhost", "-v", "DB_PORT=5432"])
    assert result.exit_code == 0
    assert "DB=localhost" in result.output
    assert "PORT=5432" in result.output


def test_render_to_file(runner: CliRunner, template_file: Path, tmp_path: Path):
    out = tmp_path / ".env"
    result = runner.invoke(template_cli, ["render", str(template_file), "-o", str(out), "-v", "DB_HOST=db", "-v", "DB_PORT=3306"])
    assert result.exit_code == 0
    assert out.exists()
    assert "DB=db" in out.read_text()


def test_render_warns_on_missing(runner: CliRunner, template_file: Path):
    result = runner.invoke(template_cli, ["render", str(template_file)])
    assert result.exit_code == 0
    assert "unresolved" in result.output or "Warning" in result.output


def test_render_from_env_file(runner: CliRunner, template_file: Path, tmp_path: Path):
    env_file = tmp_path / "base.env"
    env_file.write_text("DB_HOST=remotehost\nDB_PORT=5433\n", encoding="utf-8")
    result = runner.invoke(template_cli, ["render", str(template_file), "--env-file", str(env_file)])
    assert result.exit_code == 0
    assert "DB=remotehost" in result.output


def test_render_bad_var_format(runner: CliRunner, template_file: Path):
    result = runner.invoke(template_cli, ["render", str(template_file), "-v", "BADVALUE"])
    assert result.exit_code != 0


def test_inspect_lists_placeholders(runner: CliRunner, template_file: Path):
    result = runner.invoke(template_cli, ["inspect", str(template_file)])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "DB_PORT" in result.output


def test_inspect_no_placeholders(runner: CliRunner, tmp_path: Path):
    plain = tmp_path / "plain.env"
    plain.write_text("KEY=value\n", encoding="utf-8")
    result = runner.invoke(template_cli, ["inspect", str(plain)])
    assert result.exit_code == 0
    assert "No placeholders" in result.output
