"""Tests for envoy.lock."""

import time

import pytest

from envoy.lock import LockManager, LockResult


@pytest.fixture
def manager(tmp_path):
    return LockManager(lock_dir=tmp_path / "locks")


# ---------------------------------------------------------------------------
# LockResult
# ---------------------------------------------------------------------------

def test_lock_result_bool_true():
    assert bool(LockResult(action="acquire", key="k", success=True)) is True


def test_lock_result_bool_false():
    assert bool(LockResult(action="acquire", key="k", success=False, error="x")) is False


def test_lock_result_repr_contains_action_and_key():
    r = LockResult(action="release", key="mykey", success=True)
    assert "release" in repr(r)
    assert "mykey" in repr(r)


# ---------------------------------------------------------------------------
# acquire / release
# ---------------------------------------------------------------------------

def test_acquire_returns_success(manager):
    result = manager.acquire("project/dev", owner="alice")
    assert result.success
    assert result.action == "acquire"


def test_acquire_twice_fails(manager):
    manager.acquire("project/dev", owner="alice", ttl=60)
    result = manager.acquire("project/dev", owner="bob", ttl=60)
    assert not result.success
    assert "alice" in (result.error or "")


def test_acquire_expired_lock_succeeds(manager):
    # Acquire with ttl=0 so it expires immediately
    manager.acquire("project/dev", owner="alice", ttl=0)
    time.sleep(0.05)
    result = manager.acquire("project/dev", owner="bob", ttl=60)
    assert result.success


def test_release_removes_lock(manager):
    manager.acquire("project/dev", ttl=60)
    result = manager.release("project/dev")
    assert result.success
    assert not manager.is_locked("project/dev")


def test_release_nonexistent_lock_fails(manager):
    result = manager.release("project/dev")
    assert not result.success
    assert result.error == "no lock found"


# ---------------------------------------------------------------------------
# is_locked
# ---------------------------------------------------------------------------

def test_is_locked_true_when_active(manager):
    manager.acquire("x", ttl=60)
    assert manager.is_locked("x") is True


def test_is_locked_false_when_missing(manager):
    assert manager.is_locked("nonexistent") is False


# ---------------------------------------------------------------------------
# list_locks
# ---------------------------------------------------------------------------

def test_list_locks_empty(manager):
    assert manager.list_locks() == []


def test_list_locks_returns_entries(manager):
    manager.acquire("proj/staging", owner="ci", ttl=120)
    manager.acquire("proj/prod", owner="deploy", ttl=120)
    locks = manager.list_locks()
    assert len(locks) == 2
    keys = {l["key"] for l in locks}
    assert "proj/staging" in keys
    assert "proj/prod" in keys


def test_list_locks_marks_expired(manager):
    manager.acquire("old", ttl=0)
    time.sleep(0.05)
    locks = manager.list_locks()
    assert locks[0]["expired"] is True
