"""Tests for envoy.cli_validate CLI commands."""
import pytest
from click.testing import CliRunner
from pathlib import Path

from envoy.cli_validate import validate_cli


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def tmp_files(tmp_path):
    schema = tmp_path / "schema.env"
    schema.write_text("DB_HOST=required\nDB_PORT=required\nOPTIONAL=?optional\n")
    env_ok = tmp_path / "ok.env"
    env_ok.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    env_bad = tmp_path / "bad.env"
    env_bad.write_text("DB_HOST=localhost\n")
    return {"schema": schema, "ok": env_ok, "bad": env_bad, "dir": tmp_path}


def test_check_valid_env_exits_zero(runner, tmp_files):
    result = runner.invoke(
        validate_cli, ["check", str(tmp_files["ok"]), str(tmp_files["schema"])]
    )
    assert result.exit_code == 0
    assert "All required keys" in result.output


def test_check_invalid_env_exits_nonzero(runner, tmp_files):
    result = runner.invoke(
        validate_cli, ["check", str(tmp_files["bad"]), str(tmp_files["schema"])]
    )
    assert result.exit_code == 1
    assert "FAILED" in result.output


def test_check_strict_flags_extra_keys(runner, tmp_files):
    extra = tmp_files["dir"] / "extra.env"
    extra.write_text("DB_HOST=h\nDB_PORT=5\nUNKNOWN=foo\n")
    result = runner.invoke(
        validate_cli,
        ["check", str(extra), str(tmp_files["schema"]), "--strict"],
    )
    assert "UNKNOWN" in result.output


def test_show_schema_lists_keys(runner, tmp_files):
    result = runner.invoke(validate_cli, ["show-schema", str(tmp_files["schema"])])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "DB_PORT" in result.output
    assert "OPTIONAL" in result.output
    assert "optional" in result.output
    assert "required" in result.output
