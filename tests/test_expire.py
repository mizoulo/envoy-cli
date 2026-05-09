"""Tests for envoy.expire."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from envoy.expire import ExpireManager, ExpireResult


@pytest.fixture()
def manager(tmp_path: Path) -> ExpireManager:
    return ExpireManager(tmp_path / "expire_store")


def test_expire_result_success_when_no_error():
    r = ExpireResult(action="set", key="MY_KEY")
    assert r.success() is True


def test_expire_result_failure_when_error():
    r = ExpireResult(action="set", key="MY_KEY", error="oops")
    assert r.success() is False


def test_expire_result_repr_contains_action_and_key():
    r = ExpireResult(action="clear", key="DB_PASS")
    assert "clear" in repr(r)
    assert "DB_PASS" in repr(r)


def test_set_expiry_creates_index_file(manager: ExpireManager, tmp_path: Path):
    manager.set_expiry("API_KEY", ttl_seconds=60)
    assert (tmp_path / "expire_store" / "expire_index.json").exists()


def test_set_expiry_returns_success(manager: ExpireManager):
    result = manager.set_expiry("TOKEN", ttl_seconds=300)
    assert result.success()
    assert result.action == "set"
    assert result.key == "TOKEN"


def test_key_not_expired_before_ttl(manager: ExpireManager):
    manager.set_expiry("X", ttl_seconds=9999)
    assert manager.is_expired("X") is False


def test_key_expired_after_ttl(manager: ExpireManager):
    manager.set_expiry("X", ttl_seconds=-1)  # already in the past
    assert manager.is_expired("X") is True


def test_unknown_key_not_expired(manager: ExpireManager):
    assert manager.is_expired("NONEXISTENT") is False


def test_expiry_time_returns_timestamp(manager: ExpireManager):
    before = time.time()
    manager.set_expiry("K", ttl_seconds=100)
    exp = manager.expiry_time("K")
    assert exp is not None
    assert exp >= before + 99


def test_expiry_time_none_for_unknown(manager: ExpireManager):
    assert manager.expiry_time("MISSING") is None


def test_clear_expiry_removes_key(manager: ExpireManager):
    manager.set_expiry("Z", ttl_seconds=500)
    result = manager.clear_expiry("Z")
    assert result.success()
    assert manager.expiry_time("Z") is None


def test_clear_expiry_missing_key_returns_error(manager: ExpireManager):
    result = manager.clear_expiry("GHOST")
    assert not result.success()
    assert "not found" in result.error


def test_expired_keys_returns_only_past(manager: ExpireManager):
    manager.set_expiry("OLD", ttl_seconds=-5)
    manager.set_expiry("NEW", ttl_seconds=9999)
    expired = manager.expired_keys()
    assert "OLD" in expired
    assert "NEW" not in expired


def test_index_persists_across_instances(tmp_path: Path):
    store = tmp_path / "store"
    m1 = ExpireManager(store)
    m1.set_expiry("PERSIST", ttl_seconds=600)
    m2 = ExpireManager(store)
    assert m2.expiry_time("PERSIST") is not None
