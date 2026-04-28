"""Sync engine for pushing/pulling .env files between local projects and vault."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from envoy.vault import Vault
from envoy.config import Config


class SyncResult:
    """Represents the outcome of a sync operation."""

    def __init__(self, env_name: str, direction: str, success: bool, message: str = ""):
        self.env_name = env_name
        self.direction = direction  # 'push' or 'pull'
        self.success = success
        self.message = message

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"SyncResult({self.direction} {self.env_name!r}: {status} — {self.message})"


class SyncEngine:
    """Coordinates syncing .env files between a local directory and a Vault."""

    def __init__(self, vault: Vault, config: Config):
        self.vault = vault
        self.config = config

    def push_file(self, env_name: str, file_path: Path) -> SyncResult:
        """Push a local .env file to the vault."""
        if not file_path.exists():
            return SyncResult(env_name, "push", False, f"File not found: {file_path}")
        try:
            data = file_path.read_bytes()
            self.vault.push(env_name, data)
            return SyncResult(env_name, "push", True, f"Pushed {len(data)} bytes")
        except Exception as exc:
            return SyncResult(env_name, "push", False, str(exc))

    def pull_file(self, env_name: str, dest_path: Path) -> SyncResult:
        """Pull an env from the vault and write it to dest_path."""
        try:
            data = self.vault.pull(env_name)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(data)
            return SyncResult(env_name, "pull", True, f"Written to {dest_path}")
        except KeyError:
            return SyncResult(env_name, "pull", False, f"Env {env_name!r} not found in vault")
        except Exception as exc:
            return SyncResult(env_name, "pull", False, str(exc))

    def sync_all(self, direction: str, base_dir: Path) -> list[SyncResult]:
        """Push or pull every env tracked in the vault."""
        if direction not in ("push", "pull"):
            raise ValueError(f"direction must be 'push' or 'pull', got {direction!r}")
        results: list[SyncResult] = []
        for env_name in self.vault.list_envs():
            file_path = base_dir / f".env.{env_name}"
            if direction == "push":
                results.append(self.push_file(env_name, file_path))
            else:
                results.append(self.pull_file(env_name, file_path))
        return results
