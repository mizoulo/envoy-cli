"""Tests for envoy.scope."""
import pytest
from pathlib import Path

from envoy.vault import Vault
from envoy.storage import LocalStorage
from envoy.scope import ScopeManager, ScopeResult


PASSWORD = "test-secret"


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    storage = LocalStorage(tmp_path)
    return Vault(storage)


@pytest.fixture()
def manager(vault: Vault) -> ScopeManager:
    return ScopeManager(vault, "team-a")


def test_scope_result_success():
    r = ScopeResult(action="push", scope="team-a", ok=True)
    assert r.success is True
    assert "ok" in repr(r)


def test_scope_result_failure():
    r = ScopeResult(action="pull", scope="team-a", ok=False, error="not found")
    assert r.success is False
    assert "error=not found" in repr(r)


def test_push_returns_success(manager: ScopeManager):
    result = manager.push("myapp", "production", "KEY=val", PASSWORD)
    assert result.success
    assert result.scope == "team-a"
    assert result.action == "push"


def test_pull_round_trip(manager: ScopeManager):
    manager.push("myapp", "production", "KEY=hello", PASSWORD)
    result, content = manager.pull("myapp", "production", PASSWORD)
    assert result.success
    assert content == "KEY=hello"


def test_pull_wrong_password_fails(manager: ScopeManager):
    manager.push("myapp", "staging", "KEY=secret", PASSWORD)
    result, content = manager.pull("myapp", "staging", "wrong-password")
    assert not result.success
    assert content is None


def test_list_envs_only_returns_scoped(vault: Vault):
    mgr_a = ScopeManager(vault, "team-a")
    mgr_b = ScopeManager(vault, "team-b")
    mgr_a.push("proj", "dev", "A=1", PASSWORD)
    mgr_b.push("proj", "dev", "B=2", PASSWORD)
    assert mgr_a.list_envs("proj") == ["dev"]
    assert mgr_b.list_envs("proj") == ["dev"]


def test_list_scopes_returns_all(vault: Vault):
    ScopeManager(vault, "team-a").push("proj", "dev", "X=1", PASSWORD)
    ScopeManager(vault, "team-b").push("proj", "dev", "Y=2", PASSWORD)
    mgr = ScopeManager(vault, "team-a")
    scopes = mgr.list_scopes("proj")
    assert "team-a" in scopes
    assert "team-b" in scopes


def test_list_envs_empty_when_no_pushes(manager: ScopeManager):
    assert manager.list_envs("proj") == []
