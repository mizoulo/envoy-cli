"""Tests for envoy.backup."""
from pathlib import Path

import pytest

from envoy.backup import BackupManager, BackupResult


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("API_KEY=secret\nDEBUG=true\n")
    return env


@pytest.fixture()
def manager(tmp_path: Path) -> BackupManager:
    return BackupManager(backup_dir=tmp_path / "backups")


# ---------------------------------------------------------------------------
# BackupResult helpers
# ---------------------------------------------------------------------------

def test_backup_result_success_when_no_error():
    r = BackupResult(action="create", archive=Path("x.tar.gz"))
    assert r.success is True


def test_backup_result_failure_when_error():
    r = BackupResult(action="create", error="boom")
    assert r.success is False


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_produces_archive(manager: BackupManager, tmp_env: Path):
    result = manager.create([tmp_env])
    assert result.success
    assert result.archive is not None
    assert result.archive.exists()
    assert result.archive.suffix == ".gz"


def test_create_with_label_includes_label(manager: BackupManager, tmp_env: Path):
    result = manager.create([tmp_env], label="staging")
    assert result.success
    assert "staging" in result.archive.name


def test_create_missing_source_returns_error(manager: BackupManager, tmp_path: Path):
    missing = tmp_path / "ghost.env"
    result = manager.create([missing])
    assert not result.success
    assert "not found" in result.error


# ---------------------------------------------------------------------------
# restore
# ---------------------------------------------------------------------------

def test_restore_round_trip(manager: BackupManager, tmp_env: Path, tmp_path: Path):
    create_result = manager.create([tmp_env])
    restore_dir = tmp_path / "restored"
    restore_result = manager.restore(create_result.archive, restore_dir)
    assert restore_result.success
    assert (restore_dir / tmp_env.name).read_text() == tmp_env.read_text()


def test_restore_missing_archive_returns_error(manager: BackupManager, tmp_path: Path):
    result = manager.restore(tmp_path / "no.tar.gz", tmp_path / "out")
    assert not result.success
    assert "not found" in result.error


# ---------------------------------------------------------------------------
# list_backups / prune
# ---------------------------------------------------------------------------

def test_list_backups_empty(manager: BackupManager):
    assert manager.list_backups() == []


def test_list_backups_returns_archives(manager: BackupManager, tmp_env: Path):
    manager.create([tmp_env])
    manager.create([tmp_env])
    assert len(manager.list_backups()) == 2


def test_prune_keeps_most_recent(manager: BackupManager, tmp_env: Path):
    for _ in range(5):
        manager.create([tmp_env])
    deleted = manager.prune(keep=3)
    assert len(deleted) == 2
    assert len(manager.list_backups()) == 3


def test_prune_noop_when_below_limit(manager: BackupManager, tmp_env: Path):
    manager.create([tmp_env])
    deleted = manager.prune(keep=5)
    assert deleted == []
