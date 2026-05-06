"""Tests for envoy.replay."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envoy.replay import ReplayEngine, ReplayResult
from envoy.audit import AuditLog, AuditEntry
from envoy.vault import Vault
from envoy.storage import LocalStorage


PASSWORD = "test-secret"


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    storage = LocalStorage(tmp_path / "vault")
    return Vault(storage=storage, default_password=PASSWORD)


@pytest.fixture()
def audit_log(tmp_path: Path) -> AuditLog:
    return AuditLog(tmp_path / "audit.json")


@pytest.fixture()
def engine(vault: Vault, audit_log: AuditLog) -> ReplayEngine:
    return ReplayEngine(vault=vault, audit_log=audit_log)


def test_replay_result_success_when_replayed():
    r = ReplayResult(action="replay_push", project="p", env="dev", replayed=True)
    assert r.success() is True


def test_replay_result_failure_when_error():
    r = ReplayResult(action="replay_push", project="p", env="dev", replayed=False, error="boom")
    assert r.success() is False


def test_replay_result_repr_contains_action_and_env():
    r = ReplayResult(action="replay_push", project="p", env="dev", replayed=True)
    assert "replay_push" in repr(r)
    assert "dev" in repr(r)
    assert "ok" in repr(r)


def test_replay_push_stores_content(engine: ReplayEngine, vault: Vault):
    result = engine.replay_push("myapp", "dev", "KEY=value\n", PASSWORD)
    assert result.success()
    pulled = vault.pull("myapp", "dev", PASSWORD)
    assert "KEY=value" in pulled


def test_replay_push_records_audit(engine: ReplayEngine, audit_log: AuditLog):
    engine.replay_push("myapp", "dev", "KEY=value\n", PASSWORD)
    entries = audit_log.all()
    assert any(e.action == "replay_push" for e in entries)


def test_replay_pull_round_trip(engine: ReplayEngine):
    engine.replay_push("myapp", "staging", "FOO=bar\n", PASSWORD)
    result = engine.replay_pull("myapp", "staging", PASSWORD)
    assert result.success()
    assert result.action == "replay_pull"


def test_replay_pull_missing_key_returns_failure(engine: ReplayEngine):
    result = engine.replay_pull("myapp", "nonexistent", PASSWORD)
    assert result.success() is False
    assert result.error is not None


def test_replay_pull_wrong_password_returns_failure(engine: ReplayEngine):
    engine.replay_push("myapp", "prod", "SECRET=x\n", PASSWORD)
    result = engine.replay_pull("myapp", "prod", "wrong-password")
    assert result.success() is False


def test_last_entry_returns_most_recent(engine: ReplayEngine, audit_log: AuditLog):
    engine.replay_push("myapp", "dev", "A=1\n", PASSWORD)
    engine.replay_push("myapp", "dev", "A=2\n", PASSWORD)
    entry = engine.last_entry("myapp", "dev", "replay_push")
    assert entry is not None
    assert entry["action"] == "replay_push"


def test_last_entry_returns_none_when_no_match(engine: ReplayEngine):
    result = engine.last_entry("ghost", "dev", "replay_push")
    assert result is None
