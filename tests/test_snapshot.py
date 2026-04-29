"""Tests for envoy.snapshot module."""

import pytest

from envoy.snapshot import Snapshot, SnapshotManager
from envoy.vault import Vault
from envoy.storage import LocalStorage


@pytest.fixture
def vault(tmp_path):
    storage = LocalStorage(tmp_path / "vault", password="test-pass")
    return Vault(storage)


@pytest.fixture
def manager(vault):
    return SnapshotManager(vault, project="myapp")


def test_snapshot_key_without_label():
    snap = Snapshot(project="p", env_name="prod", timestamp=1700000000.0, content="K=V")
    assert snap.snapshot_key == "p/prod/snapshots/1700000000"


def test_snapshot_key_with_label():
    snap = Snapshot(project="p", env_name="prod", timestamp=1700000000.0, content="K=V", label="before-deploy")
    assert snap.snapshot_key == "p/prod/snapshots/1700000000_before-deploy"


def test_snapshot_to_dict_round_trip():
    snap = Snapshot(project="p", env_name="dev", timestamp=123.0, content="A=1", label="v1")
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored.project == snap.project
    assert restored.env_name == snap.env_name
    assert restored.timestamp == snap.timestamp
    assert restored.content == snap.content
    assert restored.label == snap.label


def test_capture_stores_snapshot(manager):
    snap = manager.capture("prod", "DB=localhost", label="init")
    assert snap.project == "myapp"
    assert snap.env_name == "prod"
    assert snap.label == "init"
    assert snap.content == "DB=localhost"


def test_restore_returns_content(manager):
    snap = manager.capture("staging", "API_KEY=secret")
    ts = int(snap.timestamp)
    result = manager.restore("staging", ts)
    assert result == "API_KEY=secret"


def test_restore_with_label(manager):
    snap = manager.capture("prod", "X=1", label="pre-release")
    ts = int(snap.timestamp)
    result = manager.restore("prod", ts, label="pre-release")
    assert result == "X=1"


def test_list_snapshots_returns_matching_keys(manager):
    manager.capture("prod", "A=1")
    manager.capture("prod", "A=2")
    manager.capture("dev", "B=3")
    prod_snaps = manager.list_snapshots("prod")
    dev_snaps = manager.list_snapshots("dev")
    assert len(prod_snaps) == 2
    assert len(dev_snaps) == 1


def test_list_snapshots_empty_when_none(manager):
    result = manager.list_snapshots("nonexistent")
    assert result == []
