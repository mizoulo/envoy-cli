"""Tests for envoy.cli_namespace."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envoy.cli_namespace import namespace_cli


PASSWORD = "testpass"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / "prod.env"
    p.write_text("API_KEY=abc123\nDEBUG=false\n")
    return str(p)


# ---------------------------------------------------------------------------
# push
# ---------------------------------------------------------------------------

def test_push_outputs_confirmation(runner, vault_dir, env_file):
    result = runner.invoke(
        namespace_cli,
        ["push", "backend", "production", env_file,
         "--project", "myapp", "--storage-dir", vault_dir,
         "--password", PASSWORD],
    )
    assert result.exit_code == 0
    assert "backend/production" in result.output


# ---------------------------------------------------------------------------
# pull
# ---------------------------------------------------------------------------

def test_pull_round_trip_stdout(runner, vault_dir, env_file):
    runner.invoke(
        namespace_cli,
        ["push", "backend", "production", env_file,
         "--project", "myapp", "--storage-dir", vault_dir,
         "--password", PASSWORD],
    )
    result = runner.invoke(
        namespace_cli,
        ["pull", "backend", "production",
         "--project", "myapp", "--storage-dir", vault_dir,
         "--password", PASSWORD],
    )
    assert result.exit_code == 0
    assert "API_KEY=abc123" in result.output


def test_pull_to_file(runner, vault_dir, env_file, tmp_path):
    runner.invoke(
        namespace_cli,
        ["push", "backend", "production", env_file,
         "--project", "myapp", "--storage-dir", vault_dir,
         "--password", PASSWORD],
    )
    out = str(tmp_path / "out.env")
    result = runner.invoke(
        namespace_cli,
        ["pull", "backend", "production",
         "--project", "myapp", "--storage-dir", vault_dir,
         "--password", PASSWORD, "--output", out],
    )
    assert result.exit_code == 0
    assert "Written to" in result.output
    assert "API_KEY=abc123" in open(out).read()


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_shows_envs(runner, vault_dir, env_file):
    for env in ("production", "staging"):
        runner.invoke(
            namespace_cli,
            ["push", "backend", env, env_file,
             "--project", "myapp", "--storage-dir", vault_dir,
             "--password", PASSWORD],
        )
    result = runner.invoke(
        namespace_cli,
        ["list", "backend", "--project", "myapp", "--storage-dir", vault_dir],
    )
    assert result.exit_code == 0
    assert "production" in result.output
    assert "staging" in result.output


def test_list_empty_namespace(runner, vault_dir):
    result = runner.invoke(
        namespace_cli,
        ["list", "ghost", "--project", "myapp", "--storage-dir", vault_dir],
    )
    assert result.exit_code == 0
    assert "No envs" in result.output


# ---------------------------------------------------------------------------
# namespaces
# ---------------------------------------------------------------------------

def test_list_namespaces(runner, vault_dir, env_file):
    for ns in ("backend", "frontend"):
        runner.invoke(
            namespace_cli,
            ["push", ns, "prod", env_file,
             "--project", "myapp", "--storage-dir", vault_dir,
             "--password", PASSWORD],
        )
    result = runner.invoke(
        namespace_cli,
        ["namespaces", "--project", "myapp", "--storage-dir", vault_dir],
    )
    assert result.exit_code == 0
    assert "backend" in result.output
    assert "frontend" in result.output


def test_list_namespaces_empty(runner, vault_dir):
    result = runner.invoke(
        namespace_cli,
        ["namespaces", "--project", "myapp", "--storage-dir", vault_dir],
    )
    assert result.exit_code == 0
    assert "No namespaces" in result.output
