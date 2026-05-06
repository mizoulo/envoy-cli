"""Tests for envoy.prune."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envoy.vault import Vault
from envoy.prune import PruneResult, _is_expired, prune_project


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    return Vault(storage_dir=str(tmp_path), password="secret")


def _push(vault: Vault, project: str, env: str, content: str = "KEY=val") -> None:
    vault.push(project, env, content)


# ---------------------------------------------------------------------------
# PruneResult unit tests
# ---------------------------------------------------------------------------

def test_prune_result_success_when_no_error():
    r = PruneResult(removed=["dev"], skipped=[])
    assert r.success is True


def test_prune_result_failure_when_error():
    r = PruneResult(error="boom")
    assert r.success is False


def test_prune_result_repr_contains_counts():
    r = PruneResult(removed=["a", "b"], skipped=["c"])
    text = repr(r)
    assert "2" in text
    assert "1" in text


# ---------------------------------------------------------------------------
# _is_expired helper
# ---------------------------------------------------------------------------

def test_is_expired_old_timestamp():
    cutoff = datetime(2024, 1, 1, tzinfo=timezone.utc)
    meta = {"updated_at": "2023-06-15T10:00:00"}
    assert _is_expired(meta, cutoff) is True


def test_is_expired_fresh_timestamp():
    cutoff = datetime(2023, 1, 1, tzinfo=timezone.utc)
    meta = {"updated_at": "2024-06-15T10:00:00"}
    assert _is_expired(meta, cutoff) is False


def test_is_expired_missing_timestamp():
    assert _is_expired({}, datetime(2024, 1, 1, tzinfo=timezone.utc)) is False


# ---------------------------------------------------------------------------
# prune_project integration tests
# ---------------------------------------------------------------------------

def test_prune_removes_all_when_no_cutoff(vault: Vault):
    _push(vault, "myapp", "dev")
    _push(vault, "myapp", "prod")
    result = prune_project(vault, "myapp")
    assert result.success
    assert set(result.removed) == {"dev", "prod"}
    assert vault.list_envs("myapp") == []


def test_prune_dry_run_does_not_delete(vault: Vault):
    _push(vault, "myapp", "staging")
    result = prune_project(vault, "myapp", dry_run=True)
    assert "staging" in result.removed
    # entry still present after dry run
    assert "staging" in vault.list_envs("myapp")


def test_prune_skips_fresh_entries(vault: Vault):
    _push(vault, "myapp", "dev")
    far_past = datetime.now(timezone.utc) - timedelta(days=3650)
    result = prune_project(vault, "myapp", before=far_past)
    assert "dev" in result.skipped
    assert result.removed == []


def test_prune_unknown_project_returns_empty(vault: Vault):
    result = prune_project(vault, "ghost")
    assert result.success
    assert result.removed == []
