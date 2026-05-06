"""Tests for envoy.history."""
import json
import pytest
from pathlib import Path
from envoy.history import HistoryEntry, HistoryLog


@pytest.fixture
def log(tmp_path: Path) -> HistoryLog:
    return HistoryLog(tmp_path / "history.json")


def test_log_file_created_on_init(tmp_path: Path):
    path = tmp_path / "sub" / "history.json"
    HistoryLog(path)
    assert path.exists()
    assert json.loads(path.read_text()) == []


def test_record_single_entry(log: HistoryLog):
    entry = log.record("push", "myapp", "production")
    assert entry.action == "push"
    assert entry.project == "myapp"
    assert entry.env_name == "production"
    assert entry.note is None
    assert "T" in entry.timestamp  # ISO format


def test_record_with_note(log: HistoryLog):
    entry = log.record("pull", "myapp", "staging", note="pre-deploy")
    assert entry.note == "pre-deploy"


def test_all_returns_all_entries(log: HistoryLog):
    log.record("push", "alpha", "dev")
    log.record("pull", "beta", "prod")
    entries = log.all()
    assert len(entries) == 2
    assert entries[0].project == "alpha"
    assert entries[1].project == "beta"


def test_filter_by_project(log: HistoryLog):
    log.record("push", "alpha", "dev")
    log.record("push", "beta", "dev")
    log.record("pull", "alpha", "prod")
    result = log.filter(project="alpha")
    assert len(result) == 2
    assert all(e.project == "alpha" for e in result)


def test_filter_by_action(log: HistoryLog):
    log.record("push", "alpha", "dev")
    log.record("pull", "alpha", "dev")
    log.record("push", "beta", "prod")
    result = log.filter(action="push")
    assert len(result) == 2
    assert all(e.action == "push" for e in result)


def test_filter_by_project_and_action(log: HistoryLog):
    log.record("push", "alpha", "dev")
    log.record("pull", "alpha", "dev")
    log.record("push", "beta", "dev")
    result = log.filter(project="alpha", action="push")
    assert len(result) == 1
    assert result[0].project == "alpha"
    assert result[0].action == "push"


def test_clear_all(log: HistoryLog):
    log.record("push", "alpha", "dev")
    log.record("pull", "beta", "prod")
    removed = log.clear()
    assert removed == 2
    assert log.all() == []


def test_clear_by_project(log: HistoryLog):
    log.record("push", "alpha", "dev")
    log.record("push", "beta", "dev")
    removed = log.clear(project="alpha")
    assert removed == 1
    remaining = log.all()
    assert len(remaining) == 1
    assert remaining[0].project == "beta"


def test_entry_repr(log: HistoryLog):
    entry = log.record("push", "myapp", "production", note="hotfix")
    r = repr(entry)
    assert "push" in r
    assert "myapp" in r
    assert "production" in r
    assert "hotfix" in r


def test_entry_round_trip():
    data = {
        "action": "pull",
        "project": "proj",
        "env_name": "qa",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "note": None,
    }
    entry = HistoryEntry.from_dict(data)
    assert entry.to_dict() == data
