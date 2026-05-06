"""Tests for envoy.alias."""
from __future__ import annotations

import pytest

from envoy.alias import AliasManager, AliasResult
from envoy.vault import Vault


@pytest.fixture()
def vault(tmp_path):
    return Vault(storage_dir=str(tmp_path), password="test-secret")


@pytest.fixture()
def manager(vault):
    return AliasManager(vault, project="myapp", env="production")


# ---------------------------------------------------------------------------
# AliasResult
# ---------------------------------------------------------------------------

def test_alias_result_success_when_no_error():
    r = AliasResult("add", "DATABASE_URL", "DB_URL")
    assert r.success is True


def test_alias_result_failure_when_error():
    r = AliasResult("add", "DATABASE_URL", "DB_URL", error="already exists")
    assert r.success is False


# ---------------------------------------------------------------------------
# add / remove
# ---------------------------------------------------------------------------

def test_add_registers_alias(manager):
    result = manager.add("DATABASE_URL", "DB_URL")
    assert result.success
    assert result.action == "add"
    assert manager.list_aliases() == {"DB_URL": "DATABASE_URL"}


def test_add_duplicate_returns_error(manager):
    manager.add("DATABASE_URL", "DB_URL")
    result = manager.add("DATABASE_URL", "DB_URL")
    assert not result.success
    assert "already exists" in result.error


def test_remove_existing_alias(manager):
    manager.add("API_KEY", "KEY")
    result = manager.remove("KEY")
    assert result.success
    assert result.original == "API_KEY"
    assert manager.list_aliases() == {}


def test_remove_nonexistent_alias_returns_error(manager):
    result = manager.remove("GHOST")
    assert not result.success
    assert "not found" in result.error


# ---------------------------------------------------------------------------
# resolve
# ---------------------------------------------------------------------------

def test_resolve_known_alias(manager):
    manager.add("SECRET_KEY", "SK")
    assert manager.resolve("SK") == "SECRET_KEY"


def test_resolve_unknown_returns_itself(manager):
    assert manager.resolve("UNKNOWN") == "UNKNOWN"


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

def test_apply_rewrites_keys(manager):
    manager.add("DATABASE_URL", "DB_URL")
    manager.add("API_KEY", "KEY")
    content = "DATABASE_URL=postgres://localhost\nAPI_KEY=abc123\nOTHER=value"
    result = manager.apply(content)
    assert "DB_URL=postgres://localhost" in result
    assert "KEY=abc123" in result
    assert "OTHER=value" in result


def test_apply_preserves_comments_and_blanks(manager):
    manager.add("FOO", "BAR")
    content = "# comment\n\nFOO=1"
    result = manager.apply(content)
    assert "# comment" in result
    assert "BAR=1" in result


def test_apply_no_aliases_returns_unchanged(manager):
    content = "FOO=1\nBAR=2"
    assert manager.apply(content) == content
