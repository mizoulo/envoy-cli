"""Tests for envoy.pin — PinManager and PinResult."""
import pytest
from pathlib import Path

from envoy.pin import PinManager, PinResult


@pytest.fixture
def manager(tmp_path: Path) -> PinManager:
    return PinManager(tmp_path / "pins.json")


# ---------------------------------------------------------------------------
# PinResult
# ---------------------------------------------------------------------------

def test_pin_result_success_when_pinned():
    r = PinResult("myapp", "production", "snap:abc", "pinned")
    assert r.success is True


def test_pin_result_success_when_unpinned():
    r = PinResult("myapp", "production", None, "unpinned")
    assert r.success is True


def test_pin_result_failure_when_already_pinned():
    r = PinResult("myapp", "production", "snap:abc", "already_pinned")
    assert r.success is False


def test_pin_result_repr_contains_action():
    r = PinResult("myapp", "staging", "snap:xyz", "pinned")
    assert "pinned" in repr(r)
    assert "myapp/staging" in repr(r)


# ---------------------------------------------------------------------------
# PinManager — basic operations
# ---------------------------------------------------------------------------

def test_pin_stores_entry(manager: PinManager):
    result = manager.pin("myapp", "production", "snap:001")
    assert result.action == "pinned"
    assert manager.get_pin("myapp", "production") == "snap:001"


def test_pin_same_key_returns_already_pinned(manager: PinManager):
    manager.pin("myapp", "production", "snap:001")
    result = manager.pin("myapp", "production", "snap:001")
    assert result.action == "already_pinned"


def test_pin_overwrite_updates_entry(manager: PinManager):
    manager.pin("myapp", "production", "snap:001")
    result = manager.pin("myapp", "production", "snap:002")
    assert result.action == "pinned"
    assert manager.get_pin("myapp", "production") == "snap:002"


def test_unpin_removes_entry(manager: PinManager):
    manager.pin("myapp", "production", "snap:001")
    result = manager.unpin("myapp", "production")
    assert result.action == "unpinned"
    assert manager.get_pin("myapp", "production") is None


def test_unpin_missing_returns_not_found(manager: PinManager):
    result = manager.unpin("myapp", "production")
    assert result.action == "not_found"
    assert result.success is False


def test_get_pin_missing_returns_none(manager: PinManager):
    assert manager.get_pin("ghost", "env") is None


# ---------------------------------------------------------------------------
# PinManager — list_pins
# ---------------------------------------------------------------------------

def test_list_pins_all(manager: PinManager):
    manager.pin("app1", "prod", "snap:a")
    manager.pin("app2", "prod", "snap:b")
    pins = manager.list_pins()
    assert len(pins) == 2


def test_list_pins_filtered_by_project(manager: PinManager):
    manager.pin("app1", "prod", "snap:a")
    manager.pin("app1", "staging", "snap:b")
    manager.pin("app2", "prod", "snap:c")
    pins = manager.list_pins(project="app1")
    assert set(pins.keys()) == {"app1/prod", "app1/staging"}


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_pins_persist_across_instances(tmp_path: Path):
    store = tmp_path / "pins.json"
    m1 = PinManager(store)
    m1.pin("myapp", "prod", "snap:persisted")

    m2 = PinManager(store)
    assert m2.get_pin("myapp", "prod") == "snap:persisted"
