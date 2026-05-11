"""Tests for envoy.clone."""

from __future__ import annotations

import pytest

from envoy.vault import Vault
from envoy.clone import CloneResult, clone_env


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault(tmp_path):
    password = "test-secret"
    return Vault(storage_dir=str(tmp_path), password=password)


def _push(vault: Vault, project: str, env: str, content: str) -> None:
    vault.push(project, env, content)


# ---------------------------------------------------------------------------
# CloneResult unit tests
# ---------------------------------------------------------------------------

def test_clone_result_success_when_no_error():
    r = CloneResult(action="clone", source_project="a", source_env="prod",
                    dest_project="b", dest_env="prod")
    assert r.success is True


def test_clone_result_failure_when_error():
    r = CloneResult(action="clone", source_project="a", source_env="prod",
                    dest_project="b", dest_env="prod", error="boom")
    assert r.success is False


def test_clone_result_repr_contains_projects():
    r = CloneResult(action="clone", source_project="src", source_env="staging",
                    dest_project="dst", dest_env="staging")
    text = repr(r)
    assert "src" in text
    assert "dst" in text
    assert "staging" in text


# ---------------------------------------------------------------------------
# clone_env integration tests
# ---------------------------------------------------------------------------

def test_clone_copies_content(vault):
    _push(vault, "alpha", "prod", "KEY=value\nFOO=bar")
    result = clone_env(vault, "alpha", "prod", "beta", "prod")
    assert result.success
    assert vault.pull("beta", "prod") == "KEY=value\nFOO=bar"


def test_clone_to_different_env_name(vault):
    _push(vault, "myapp", "staging", "DB=postgres")
    result = clone_env(vault, "myapp", "staging", "myapp", "prod")
    assert result.success
    assert vault.pull("myapp", "prod") == "DB=postgres"


def test_clone_missing_source_returns_error(vault):
    result = clone_env(vault, "ghost", "prod", "other", "prod")
    assert not result.success
    assert "not found" in result.error


def test_clone_no_overwrite_by_default(vault):
    _push(vault, "proj", "prod", "A=1")
    _push(vault, "proj", "staging", "A=2")
    result = clone_env(vault, "proj", "prod", "proj", "staging")
    assert not result.success
    assert "already exists" in result.error
    # Original staging content must be untouched
    assert vault.pull("proj", "staging") == "A=2"


def test_clone_overwrite_replaces_destination(vault):
    _push(vault, "proj", "prod", "A=new")
    _push(vault, "proj", "staging", "A=old")
    result = clone_env(vault, "proj", "prod", "proj", "staging", overwrite=True)
    assert result.success
    assert vault.pull("proj", "staging") == "A=new"


def test_clone_result_records_projects_and_envs(vault):
    _push(vault, "src", "dev", "X=1")
    result = clone_env(vault, "src", "dev", "dst", "dev")
    assert result.source_project == "src"
    assert result.source_env == "dev"
    assert result.dest_project == "dst"
    assert result.dest_env == "dev"
