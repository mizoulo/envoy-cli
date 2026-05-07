"""Tests for envoy.archive."""
from __future__ import annotations

import zipfile
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from envoy.archive import ArchiveManager, ArchiveResult


PASSWORD = "test-secret"


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_vault(entries: dict):
    """Return a minimal vault-like mock populated with *entries*."""
    vault = MagicMock()
    vault.list_envs.side_effect = lambda project: list(entries.keys())
    vault.pull.side_effect = lambda project, name, pw: entries[name]
    vault.push.side_effect = lambda project, name, content, pw: None
    return vault


@pytest.fixture()
def tmp_archive(tmp_path):
    return tmp_path / "archive.zip"


# ---------------------------------------------------------------------------
# ArchiveResult unit tests
# ---------------------------------------------------------------------------

def test_archive_result_success_when_no_error():
    r = ArchiveResult(action="create", path="/tmp/a.zip", entries=["dev"])
    assert r.success is True


def test_archive_result_failure_when_error():
    r = ArchiveResult(action="create", error="boom")
    assert r.success is False


def test_archive_result_repr_contains_action_and_count():
    r = ArchiveResult(action="extract", entries=["dev", "prod"])
    assert "extract" in repr(r)
    assert "2" in repr(r)


# ---------------------------------------------------------------------------
# ArchiveManager.create
# ---------------------------------------------------------------------------

def test_create_produces_zip(tmp_archive):
    vault = _make_vault({"dev": "KEY=value\n", "prod": "KEY=prod\n"})
    mgr = ArchiveManager(vault)
    result = mgr.create("myapp", tmp_archive, PASSWORD)
    assert result.success
    assert tmp_archive.exists()
    assert set(result.entries) == {"dev", "prod"}


def test_create_zip_contains_manifest(tmp_archive):
    vault = _make_vault({"staging": "FOO=bar\n"})
    mgr = ArchiveManager(vault)
    mgr.create("myapp", tmp_archive, PASSWORD)
    with zipfile.ZipFile(tmp_archive) as zf:
        names = zf.namelist()
    assert "manifest.json" in names
    assert "staging.env" in names


def test_create_returns_error_when_no_entries():
    vault = _make_vault({})
    mgr = ArchiveManager(vault)
    result = mgr.create("empty", Path("/tmp/never.zip"), PASSWORD)
    assert not result.success
    assert "no entries" in result.error


def test_create_returns_error_on_vault_exception(tmp_archive):
    vault = MagicMock()
    vault.list_envs.side_effect = RuntimeError("storage failure")
    mgr = ArchiveManager(vault)
    result = mgr.create("myapp", tmp_archive, PASSWORD)
    assert not result.success
    assert "storage failure" in result.error


# ---------------------------------------------------------------------------
# ArchiveManager.extract
# ---------------------------------------------------------------------------

def test_extract_restores_entries(tmp_path, tmp_archive):
    vault = _make_vault({"dev": "KEY=1\n", "prod": "KEY=2\n"})
    mgr = ArchiveManager(vault)
    mgr.create("myapp", tmp_archive, PASSWORD)

    restore_vault = _make_vault({})
    restore_mgr = ArchiveManager(restore_vault)
    result = restore_mgr.extract("myapp", tmp_archive, PASSWORD)
    assert result.success
    assert set(result.entries) == {"dev", "prod"}
    assert restore_vault.push.call_count == 2


def test_extract_returns_error_when_file_missing(tmp_path):
    vault = _make_vault({})
    mgr = ArchiveManager(vault)
    result = mgr.extract("myapp", tmp_path / "missing.zip", PASSWORD)
    assert not result.success
    assert "not found" in result.error
