"""Tests for envoy.cli_quota."""
import pytest
from click.testing import CliRunner
from pathlib import Path
from envoy.cli_quota import quota_cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def quota_dir(tmp_path):
    return str(tmp_path / "quotas")


def test_set_quota_outputs_confirmation(runner, quota_dir):
    result = runner.invoke(
        quota_cli,
        ["set", "myproject", "--max-keys", "50", "--quota-dir", quota_dir],
    )
    assert result.exit_code == 0
    assert "myproject" in result.output
    assert "max_keys=50" in result.output


def test_set_quota_defaults(runner, quota_dir):
    result = runner.invoke(quota_cli, ["set", "proj", "--quota-dir", quota_dir])
    assert result.exit_code == 0
    assert "max_keys=100" in result.output
    assert "max_value_bytes=4096" in result.output


def test_show_quota_displays_values(runner, quota_dir):
    runner.invoke(
        quota_cli,
        ["set", "proj", "--max-keys", "25", "--max-value-bytes", "1024", "--quota-dir", quota_dir],
    )
    result = runner.invoke(quota_cli, ["show", "proj", "--quota-dir", quota_dir])
    assert result.exit_code == 0
    assert "25" in result.output
    assert "1024" in result.output


def test_show_quota_default_for_unknown(runner, quota_dir):
    result = runner.invoke(quota_cli, ["show", "ghost", "--quota-dir", quota_dir])
    assert result.exit_code == 0
    assert "100" in result.output


def test_remove_quota_existing(runner, quota_dir):
    runner.invoke(quota_cli, ["set", "proj", "--quota-dir", quota_dir])
    result = runner.invoke(quota_cli, ["remove", "proj", "--quota-dir", quota_dir])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_quota_nonexistent(runner, quota_dir):
    result = runner.invoke(quota_cli, ["remove", "ghost", "--quota-dir", quota_dir])
    assert result.exit_code == 0
    assert "No custom quota" in result.output
