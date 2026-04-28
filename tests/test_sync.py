"""Tests for the SyncEngine."""

from __future__ import annotations

import pytest
from pathlib import Path

from envoy.sync import SyncEngine, SyncResult
from envoy.vault import Vault
from envoy.config import Config


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    return Vault(storage_dir=tmp_path / "vault", password="test-pass")


@pytest.fixture()
def config(tmp_path: Path) -> Config:
    return Config(config_path=tmp_path / "config.toml")


@pytest.fixture()
def engine(vault: Vault, config: Config) -> SyncEngine:
    return SyncEngine(vault=vault, config=config)


def test_push_file_success(engine: SyncEngine, tmp_path: Path):
    env_file = tmp_path / ".env.production"
    env_file.write_text("DB_URL=postgres://localhost/prod")
    result = engine.push_file("production", env_file)
    assert result.success
    assert result.direction == "push"
    assert result.env_name == "production"


def test_push_file_missing_file(engine: SyncEngine, tmp_path: Path):
    result = engine.push_file("staging", tmp_path / "nonexistent.env")
    assert not result.success
    assert "not found" in result.message.lower()


def test_pull_file_success(engine: SyncEngine, tmp_path: Path):
    engine.vault.push("dev", b"SECRET=abc123")
    dest = tmp_path / "output" / ".env.dev"
    result = engine.pull_file("dev", dest)
    assert result.success
    assert dest.exists()
    assert dest.read_bytes() == b"SECRET=abc123"


def test_pull_file_missing_env(engine: SyncEngine, tmp_path: Path):
    result = engine.pull_file("ghost", tmp_path / ".env.ghost")
    assert not result.success
    assert "not found" in result.message.lower()


def test_sync_all_push(engine: SyncEngine, tmp_path: Path):
    for name in ("alpha", "beta"):
        engine.vault.push(name, f"ENV={name}".encode())
    base = tmp_path / "project"
    base.mkdir()
    for name in ("alpha", "beta"):
        (base / f".env.{name}").write_text(f"ENV={name}_updated")
    results = engine.sync_all("push", base)
    assert len(results) == 2
    assert all(r.success for r in results)


def test_sync_all_pull(engine: SyncEngine, tmp_path: Path):
    for name in ("x", "y"):
        engine.vault.push(name, f"K={name}".encode())
    base = tmp_path / "dest"
    results = engine.sync_all("pull", base)
    assert len(results) == 2
    assert all(r.success for r in results)


def test_sync_all_invalid_direction(engine: SyncEngine, tmp_path: Path):
    with pytest.raises(ValueError, match="direction"):
        engine.sync_all("upload", tmp_path)


def test_sync_result_repr():
    r = SyncResult("prod", "push", True, "done")
    assert "push" in repr(r)
    assert "prod" in repr(r)
