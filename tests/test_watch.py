"""Tests for envoy.watch."""

import time
from pathlib import Path

import pytest

from envoy.watch import EnvWatcher, WatchEvent, _file_hash


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("KEY=value\n")
    return f


def test_file_hash_returns_string(env_file: Path) -> None:
    h = _file_hash(env_file)
    assert isinstance(h, str) and len(h) == 64


def test_file_hash_missing_returns_none(tmp_path: Path) -> None:
    assert _file_hash(tmp_path / "missing.env") is None


def test_file_hash_changes_on_write(env_file: Path) -> None:
    h1 = _file_hash(env_file)
    env_file.write_text("KEY=other\n")
    h2 = _file_hash(env_file)
    assert h1 != h2


def test_add_and_check_no_change(env_file: Path) -> None:
    watcher = EnvWatcher()
    watcher.add(env_file, "myproject", "production")
    events = watcher.check_once()
    assert events == []


def test_check_detects_modification(env_file: Path) -> None:
    watcher = EnvWatcher()
    watcher.add(env_file, "myproject", "production")
    env_file.write_text("KEY=changed\n")
    events = watcher.check_once()
    assert len(events) == 1
    ev = events[0]
    assert ev.project == "myproject"
    assert ev.env_name == "production"
    assert ev.path == env_file
    assert ev.old_hash != ev.new_hash


def test_callback_invoked_on_change(env_file: Path) -> None:
    watcher = EnvWatcher()
    watcher.add(env_file, "proj", "dev")
    received: list = []
    watcher.on_change(received.append)
    env_file.write_text("NEW=1\n")
    watcher.check_once()
    assert len(received) == 1
    assert isinstance(received[0], WatchEvent)


def test_callback_not_invoked_when_no_change(env_file: Path) -> None:
    watcher = EnvWatcher()
    watcher.add(env_file, "proj", "dev")
    received: list = []
    watcher.on_change(received.append)
    watcher.check_once()
    assert received == []


def test_watch_event_repr_modified(env_file: Path) -> None:
    ev = WatchEvent(env_file, "proj", "staging", "abc", "def")
    assert "modified" in repr(ev)
    assert "proj/staging" in repr(ev)


def test_watch_event_repr_created(env_file: Path) -> None:
    ev = WatchEvent(env_file, "proj", "dev", None, "def")
    assert "created" in repr(ev)


def test_second_check_no_duplicate_events(env_file: Path) -> None:
    watcher = EnvWatcher()
    watcher.add(env_file, "proj", "dev")
    env_file.write_text("CHANGED=1\n")
    watcher.check_once()
    events2 = watcher.check_once()
    assert events2 == []


def test_run_stops_after_max_iterations(env_file: Path) -> None:
    watcher = EnvWatcher(interval=0.0)
    watcher.add(env_file, "proj", "dev")
    # Should return without hanging
    watcher.run(max_iterations=3)
