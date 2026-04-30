"""Tests for envoy.cli_search."""
import os
import pytest
from click.testing import CliRunner

from envoy.cli_search import search_cli
from envoy.vault import Vault


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _populate(vault_dir: str, password: str = "pw") -> None:
    v = Vault(storage_dir=vault_dir)
    v.push("myapp", "production", "DB_HOST=prod.db\nSECRET=abc\n", password)
    v.push("myapp", "staging", "DB_HOST=staging.db\nDEBUG=true\n", password)


def test_grep_finds_matches(runner, vault_dir, monkeypatch):
    monkeypatch.setenv("ENVOY_STORAGE_DIR", vault_dir)
    _populate(vault_dir)
    result = runner.invoke(
        search_cli,
        ["grep", "DB_HOST", "--project", "myapp", "--password", "pw"],
    )
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "2 match" in result.output


def test_grep_no_matches(runner, vault_dir, monkeypatch):
    monkeypatch.setenv("ENVOY_STORAGE_DIR", vault_dir)
    _populate(vault_dir)
    result = runner.invoke(
        search_cli,
        ["grep", "NOPE_KEY", "--project", "myapp", "--password", "pw"],
    )
    assert result.exit_code == 0
    assert "No matches" in result.output


def test_grep_ignore_case(runner, vault_dir, monkeypatch):
    monkeypatch.setenv("ENVOY_STORAGE_DIR", vault_dir)
    _populate(vault_dir)
    result = runner.invoke(
        search_cli,
        ["grep", "debug", "--project", "myapp", "--ignore-case", "--password", "pw"],
    )
    assert result.exit_code == 0
    assert "DEBUG=true" in result.output


def test_list_keys_success(runner, vault_dir, monkeypatch):
    monkeypatch.setenv("ENVOY_STORAGE_DIR", vault_dir)
    _populate(vault_dir)
    result = runner.invoke(
        search_cli,
        ["list-keys", "--project", "myapp", "--env", "production", "--password", "pw"],
    )
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "SECRET" in result.output


def test_list_keys_missing_env(runner, vault_dir, monkeypatch):
    monkeypatch.setenv("ENVOY_STORAGE_DIR", vault_dir)
    _populate(vault_dir)
    result = runner.invoke(
        search_cli,
        ["list-keys", "--project", "myapp", "--env", "ghost", "--password", "pw"],
    )
    assert result.exit_code != 0
