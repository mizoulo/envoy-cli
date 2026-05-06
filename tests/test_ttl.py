"""Tests for envoy.ttl module."""
import time

import pytest

from envoy.storage import LocalStorage
from envoy.ttl import TTLManager, TTLResult


@pytest.fixture
def storage(tmp_path):
    return LocalStorage(tmp_path)


@pytest.fixture
def manager(storage):
    return TTLManager(storage)


def test_ttl_result_success_when_no_error():
    r = TTLResult(action="set", key="proj/dev")
    assert r.success() is True


def test_ttl_result_failure_when_error():
    r = TTLResult(action="set", key="proj/dev", error="boom")
    assert r.success() is False


def test_ttl_result_repr_contains_action_and_key():
    r = TTLResult(action="clear", key="proj/prod")
    assert "clear" in repr(r)
    assert "proj/prod" in repr(r)


def test_set_ttl_returns_success(manager):
    result = manager.set_ttl("myproject", "dev", seconds=3600)
    assert result.success()
    assert result.action == "set"


def test_get_expiry_after_set(manager):
    before = time.time()
    manager.set_ttl("myproject", "dev", seconds=60)
    expiry = manager.get_expiry("myproject", "dev")
    assert expiry is not None
    assert expiry > before
    assert expiry <= before + 65  # small slack


def test_get_expiry_missing_returns_none(manager):
    assert manager.get_expiry("ghost", "staging") is None


def test_is_expired_false_for_future_ttl(manager):
    manager.set_ttl("p", "e", seconds=9999)
    assert manager.is_expired("p", "e") is False


def test_is_expired_true_for_past_ttl(manager):
    manager.set_ttl("p", "e", seconds=-1)  # already expired
    assert manager.is_expired("p", "e") is True


def test_is_expired_false_when_no_ttl_set(manager):
    assert manager.is_expired("no", "ttl") is False


def test_clear_ttl_removes_entry(manager):
    manager.set_ttl("p", "e", seconds=100)
    result = manager.clear_ttl("p", "e")
    assert result.success()
    assert manager.get_expiry("p", "e") is None


def test_clear_ttl_nonexistent_is_ok(manager):
    result = manager.clear_ttl("ghost", "env")
    assert result.success()


def test_list_expiring_returns_all_entries(manager):
    manager.set_ttl("a", "dev", seconds=100)
    manager.set_ttl("b", "prod", seconds=-1)
    entries = manager.list_expiring()
    assert len(entries) == 2
    keys = {e["key"] for e in entries}
    assert "a/dev" in keys
    assert "b/prod" in keys


def test_list_expiring_expired_flag(manager):
    manager.set_ttl("x", "e", seconds=-10)
    entries = manager.list_expiring()
    assert entries[0]["expired"] is True
    assert entries[0]["remaining"] == 0.0
