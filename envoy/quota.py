"""Quota management for envoy-cli: enforce limits on keys per project/environment."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
import json
from pathlib import Path


@dataclass
class QuotaResult:
    action: str
    key: str
    allowed: bool
    reason: str = ""

    def success(self) -> bool:
        return self.allowed

    def __repr__(self) -> str:
        status = "allowed" if self.allowed else "denied"
        return f"<QuotaResult action={self.action!r} key={self.key!r} status={status} reason={self.reason!r}>"


@dataclass
class QuotaPolicy:
    max_keys: int = 100
    max_value_bytes: int = 4096
    max_key_length: int = 128

    def to_dict(self) -> Dict:
        return {
            "max_keys": self.max_keys,
            "max_value_bytes": self.max_value_bytes,
            "max_key_length": self.max_key_length,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "QuotaPolicy":
        return cls(
            max_keys=data.get("max_keys", 100),
            max_value_bytes=data.get("max_value_bytes", 4096),
            max_key_length=data.get("max_key_length", 128),
        )


class QuotaManager:
    def __init__(self, policy_path: Path) -> None:
        self._path = policy_path
        self._policies: Dict[str, QuotaPolicy] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            data = json.loads(self._path.read_text())
            self._policies = {
                k: QuotaPolicy.from_dict(v) for k, v in data.items()
            }

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._policies.items()}, indent=2)
        )

    def set_policy(self, project: str, policy: QuotaPolicy) -> None:
        self._policies[project] = policy
        self._save()

    def get_policy(self, project: str) -> QuotaPolicy:
        return self._policies.get(project, QuotaPolicy())

    def check_add_key(
        self, project: str, key: str, value: str, current_keys: int
    ) -> QuotaResult:
        policy = self.get_policy(project)
        if len(key) > policy.max_key_length:
            return QuotaResult(
                action="add", key=key, allowed=False,
                reason=f"key length {len(key)} exceeds max {policy.max_key_length}",
            )
        if len(value.encode()) > policy.max_value_bytes:
            return QuotaResult(
                action="add", key=key, allowed=False,
                reason=f"value size {len(value.encode())}B exceeds max {policy.max_value_bytes}B",
            )
        if current_keys >= policy.max_keys:
            return QuotaResult(
                action="add", key=key, allowed=False,
                reason=f"key count {current_keys} at max {policy.max_keys}",
            )
        return QuotaResult(action="add", key=key, allowed=True)

    def remove_policy(self, project: str) -> bool:
        if project in self._policies:
            del self._policies[project]
            self._save()
            return True
        return False
