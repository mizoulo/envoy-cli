"""Snapshot support: capture and restore point-in-time .env state."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from envoy.vault import Vault


@dataclass
class Snapshot:
    project: str
    env_name: str
    timestamp: float
    content: str
    label: Optional[str] = None

    @property
    def snapshot_key(self) -> str:
        label_part = f"_{self.label}" if self.label else ""
        return f"{self.project}/{self.env_name}/snapshots/{int(self.timestamp)}{label_part}"

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "env_name": self.env_name,
            "timestamp": self.timestamp,
            "content": self.content,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            project=data["project"],
            env_name=data["env_name"],
            timestamp=data["timestamp"],
            content=data["content"],
            label=data.get("label"),
        )


class SnapshotManager:
    def __init__(self, vault: Vault, project: str) -> None:
        self.vault = vault
        self.project = project

    def capture(self, env_name: str, content: str, label: Optional[str] = None) -> Snapshot:
        snap = Snapshot(
            project=self.project,
            env_name=env_name,
            timestamp=time.time(),
            content=content,
            label=label,
        )
        self.vault.push(snap.snapshot_key, snap.content)
        return snap

    def restore(self, env_name: str, timestamp: int, label: Optional[str] = None) -> str:
        label_part = f"_{label}" if label else ""
        key = f"{self.project}/{env_name}/snapshots/{timestamp}{label_part}"
        return self.vault.pull(key)

    def list_snapshots(self, env_name: str) -> List[str]:
        prefix = f"{self.project}/{env_name}/snapshots/"
        all_keys = self.vault.list_envs()
        return [k for k in all_keys if k.startswith(prefix)]
