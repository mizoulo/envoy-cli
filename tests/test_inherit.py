"""Tests for envoy.inherit."""

from __future__ import annotations

import pytest

from envoy.vault import Vault
from envoy.inherit import InheritResult, _parse_env, _serialize_env, inherit_env


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------

def test_parse_env_basic():
    text = "FOO=bar\nBAZ=qux"
    assert _parse_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments_and_blanks():
    text = "# comment\n\nFOO=bar"
    assert _parse_env(text) == {"FOO": "bar"}


def test_serialize_env_round_trip():
    pairs = {"A": "1", "B": "2"}
    assert _parse_env(_serialize_env(pairs)) == pairs


# ---------------------------------------------------------------------------
# InheritResult tests
# ---------------------------------------------------------------------------

def test_inherit_result_success_when_no_error():
    r = InheritResult(action="inherit", parent="base", child="dev", inherited=["X"])
    assert r.success is True


def test_inherit_result_failure_when_error():
    r = InheritResult(action="inherit", parent="base", child="dev", error="oops")
    assert r.success is False


def test_inherit_result_repr_contains_counts():
    r = InheritResult(
        action="inherit", parent="base", child="dev",
        inherited=["A", "B"], overridden=["C"],
    )
    text = repr(r)
    assert "inherited=2" in text
    assert "overridden=1" in text


# ---------------------------------------------------------------------------
# Integration tests using a real Vault on tmp storage
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault(tmp_path):
    return Vault(storage_dir=str(tmp_path))


PASSWORD = "test-secret"


def test_inherit_adds_parent_keys_to_child(vault):
    vault.push("myapp", "base", "HOST=localhost\nPORT=5432", PASSWORD)
    vault.push("myapp", "dev", "DEBUG=true", PASSWORD)

    result = inherit_env(vault, "myapp", "base", "dev", PASSWORD)

    assert result.success
    assert "HOST" in result.inherited
    assert "PORT" in result.inherited
    assert "DEBUG" not in result.inherited

    merged_text = vault.pull("myapp", "dev", PASSWORD)
    merged = _parse_env(merged_text)
    assert merged["HOST"] == "localhost"
    assert merged["DEBUG"] == "true"


def test_inherit_child_keys_take_priority(vault):
    vault.push("myapp", "base", "HOST=prod-host\nPORT=5432", PASSWORD)
    vault.push("myapp", "dev", "HOST=localhost", PASSWORD)

    result = inherit_env(vault, "myapp", "base", "dev", PASSWORD)

    assert result.success
    assert "HOST" in result.overridden

    merged = _parse_env(vault.pull("myapp", "dev", PASSWORD))
    assert merged["HOST"] == "localhost"
    assert merged["PORT"] == "5432"


def test_inherit_empty_child_gets_all_parent_keys(vault):
    vault.push("myapp", "base", "A=1\nB=2", PASSWORD)

    result = inherit_env(vault, "myapp", "base", "staging", PASSWORD)

    assert result.success
    assert set(result.inherited) == {"A", "B"}
    assert result.overridden == []


def test_inherit_missing_parent_returns_failure(vault):
    result = inherit_env(vault, "myapp", "nonexistent", "dev", PASSWORD)

    assert not result.success
    assert "nonexistent" in result.error
