"""Tests for envoy.audit module."""

from __future__ import annotations

import pytest
from pathlib import Path

from envoy.audit import AuditEntry, AuditLog


@pytest.fixture
def log(tmp_path: Path) -> AuditLog:
    return AuditLog(tmp_path / "audit" / "audit.log")


def test_log_file_created_on_init(tmp_path: Path) -> None:
    log_path = tmp_path / "sub" / "audit.log"
    AuditLog(log_path)
    assert log_path.exists()


def test_record_single_entry(log: AuditLog) -> None:
    entry = AuditEntry(action="push", env_name="production", project="myapp")
    log.record(entry)
    entries = log.entries()
    assert len(entries) == 1
    assert entries[0].action == "push"
    assert entries[0].env_name == "production"
    assert entries[0].project == "myapp"


def test_record_multiple_entries(log: AuditLog) -> None:
    log.record(AuditEntry(action="push", env_name="dev", project="alpha"))
    log.record(AuditEntry(action="pull", env_name="staging", project="beta"))
    log.record(AuditEntry(action="delete", env_name="dev", project="alpha"))
    assert len(log.entries()) == 3


def test_filter_by_project(log: AuditLog) -> None:
    log.record(AuditEntry(action="push", env_name="dev", project="alpha"))
    log.record(AuditEntry(action="push", env_name="dev", project="beta"))
    results = log.entries(project="alpha")
    assert len(results) == 1
    assert results[0].project == "alpha"


def test_filter_by_action(log: AuditLog) -> None:
    log.record(AuditEntry(action="push", env_name="dev", project="alpha"))
    log.record(AuditEntry(action="pull", env_name="dev", project="alpha"))
    results = log.entries(action="pull")
    assert len(results) == 1
    assert results[0].action == "pull"


def test_filter_by_project_and_action(log: AuditLog) -> None:
    log.record(AuditEntry(action="push", env_name="dev", project="alpha"))
    log.record(AuditEntry(action="pull", env_name="dev", project="alpha"))
    log.record(AuditEntry(action="push", env_name="dev", project="beta"))
    results = log.entries(project="alpha", action="push")
    assert len(results) == 1


def test_clear_removes_all_entries(log: AuditLog) -> None:
    log.record(AuditEntry(action="push", env_name="dev", project="alpha"))
    log.clear()
    assert log.entries() == []


def test_entry_repr_contains_action_and_names() -> None:
    entry = AuditEntry(action="push", env_name="prod", project="myapp", details="ok")
    text = repr(entry)
    assert "PUSH" in text
    assert "myapp/prod" in text
    assert "ok" in text


def test_entry_round_trip_serialization() -> None:
    entry = AuditEntry(action="pull", env_name="staging", project="svc", user="alice")
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.action == entry.action
    assert restored.user == entry.user
    assert restored.timestamp == entry.timestamp
