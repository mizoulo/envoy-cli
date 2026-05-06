"""Tests for envoy.namespace."""
from __future__ import annotations

import pytest

from envoy.namespace import NamespaceManager, NamespaceResult
from envoy.vault import Vault


PASSWORD = "s3cret"


@pytest.fixture()
def vault(tmp_path):
    return Vault(project="myproject", storage_dir=str(tmp_path))


@pytest.fixture()
def manager(vault):
    return NamespaceManager(vault)


# ---------------------------------------------------------------------------
# NamespaceResult
# ---------------------------------------------------------------------------

def test_namespace_result_success():
    r = NamespaceResult(action="push", namespace="backend", success=True)
    assert r.success is True
    assert "push" in repr(r)
    assert "backend" in repr(r)


def test_namespace_result_failure():
    r = NamespaceResult(action="push", namespace="backend", success=False, error="boom")
    assert r.success is False
    assert "err=boom" in repr(r)


# ---------------------------------------------------------------------------
# push / pull round-trip
# ---------------------------------------------------------------------------

def test_push_returns_success(manager):
    result = manager.push("backend", "production", "KEY=val", PASSWORD)
    assert result.success is True
    assert result.action == "push"
    assert result.namespace == "backend"


def test_pull_round_trip(manager):
    content = "DB_URL=postgres://localhost/mydb"
    manager.push("backend", "staging", content, PASSWORD)
    pulled = manager.pull("backend", "staging", PASSWORD)
    assert pulled == content


def test_pull_wrong_password_raises(manager):
    manager.push("backend", "production", "SECRET=abc", PASSWORD)
    with pytest.raises(Exception):
        manager.pull("backend", "production", "wrongpass")


# ---------------------------------------------------------------------------
# list_envs
# ---------------------------------------------------------------------------

def test_list_envs_returns_only_matching_namespace(manager):
    manager.push("backend", "prod", "A=1", PASSWORD)
    manager.push("backend", "staging", "B=2", PASSWORD)
    manager.push("frontend", "prod", "C=3", PASSWORD)

    envs = manager.list_envs("backend")
    assert sorted(envs) == ["prod", "staging"]


def test_list_envs_empty_namespace(manager):
    assert manager.list_envs("nonexistent") == []


# ---------------------------------------------------------------------------
# list_namespaces
# ---------------------------------------------------------------------------

def test_list_namespaces(manager):
    manager.push("backend", "prod", "A=1", PASSWORD)
    manager.push("frontend", "prod", "B=2", PASSWORD)
    manager.push("infra", "dev", "C=3", PASSWORD)

    ns = manager.list_namespaces()
    assert sorted(ns) == ["backend", "frontend", "infra"]


def test_list_namespaces_empty_vault(manager):
    assert manager.list_namespaces() == []


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_removes_env(manager):
    manager.push("backend", "prod", "A=1", PASSWORD)
    result = manager.delete("backend", "prod")
    assert result.success is True
    assert manager.list_envs("backend") == []


def test_delete_nonexistent_returns_failure(manager):
    result = manager.delete("backend", "ghost")
    assert result.success is False
    assert result.error is not None
