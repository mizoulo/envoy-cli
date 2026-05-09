"""Expiration management for env entries stored in the vault."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ExpireResult:
    action: str
    key: str
    error: Optional[str] = None

    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:
        status = "ok" if self.success() else f"error={self.error}"
        return f"<ExpireResult action={self.action} key={self.key} {status}>"


class ExpireManager:
    """Attach and evaluate expiration timestamps on vault keys."""

    def __init__(self, store_path: Path) -> None:
        self._path = store_path
        self._path.mkdir(parents=True, exist_ok=True)
        self._index_file = self._path / "expire_index.json"
        self._index: dict[str, float] = self._load()

    def _load(self) -> dict[str, float]:
        if self._index_file.exists():
            return json.loads(self._index_file.read_text())
        return {}

    def _save(self) -> None:
        self._index_file.write_text(json.dumps(self._index, indent=2))

    def set_expiry(self, key: str, ttl_seconds: float) -> ExpireResult:
        """Mark *key* to expire *ttl_seconds* from now."""
        try:
            self._index[key] = time.time() + ttl_seconds
            self._save()
            return ExpireResult(action="set", key=key)
        except Exception as exc:  # pragma: no cover
            return ExpireResult(action="set", key=key, error=str(exc))

    def clear_expiry(self, key: str) -> ExpireResult:
        """Remove any expiration for *key*."""
        if key not in self._index:
            return ExpireResult(action="clear", key=key, error="key not found")
        del self._index[key]
        self._save()
        return ExpireResult(action="clear", key=key)

    def is_expired(self, key: str) -> bool:
        """Return True if *key* has a recorded expiry that has passed."""
        if key not in self._index:
            return False
        return time.time() >= self._index[key]

    def expiry_time(self, key: str) -> Optional[float]:
        """Return the UNIX timestamp at which *key* expires, or None."""
        return self._index.get(key)

    def expired_keys(self) -> list[str]:
        """Return all keys whose expiry has passed."""
        now = time.time()
        return [k for k, exp in self._index.items() if now >= exp]
