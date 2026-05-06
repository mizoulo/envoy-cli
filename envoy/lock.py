"""Lock management for .env files — prevent accidental overwrites during push/pull."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class LockResult:
    action: str
    key: str
    success: bool
    error: Optional[str] = None

    def __bool__(self) -> bool:
        return self.success

    def __repr__(self) -> str:
        status = "ok" if self.success else f"err={self.error}"
        return f"LockResult(action={self.action!r}, key={self.key!r}, {status})"


class LockManager:
    """Manages advisory locks stored alongside vault metadata."""

    def __init__(self, lock_dir: Path) -> None:
        self._dir = Path(lock_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _lock_path(self, key: str) -> Path:
        safe = key.replace("/", "__").replace("\\", "__")
        return self._dir / f"{safe}.lock"

    def acquire(self, key: str, owner: str = "envoy", ttl: int = 300) -> LockResult:
        """Acquire a lock for *key*. Fails if an unexpired lock already exists."""
        path = self._lock_path(key)
        if path.exists():
            try:
                data = json.loads(path.read_text())
                expires_at = data.get("expires_at", 0)
                if time.time() < expires_at:
                    return LockResult(
                        action="acquire",
                        key=key,
                        success=False,
                        error=f"locked by {data.get('owner')!r} until {expires_at}",
                    )
            except (json.JSONDecodeError, OSError):
                pass  # corrupt lock — overwrite it

        payload = {"owner": owner, "acquired_at": time.time(), "expires_at": time.time() + ttl}
        path.write_text(json.dumps(payload))
        return LockResult(action="acquire", key=key, success=True)

    def release(self, key: str) -> LockResult:
        """Release an existing lock for *key*."""
        path = self._lock_path(key)
        if not path.exists():
            return LockResult(action="release", key=key, success=False, error="no lock found")
        path.unlink()
        return LockResult(action="release", key=key, success=True)

    def is_locked(self, key: str) -> bool:
        """Return True if *key* has an unexpired lock."""
        path = self._lock_path(key)
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text())
            return time.time() < data.get("expires_at", 0)
        except (json.JSONDecodeError, OSError):
            return False

    def list_locks(self) -> list[dict]:
        """Return metadata for all current (possibly expired) locks."""
        locks = []
        for p in sorted(self._dir.glob("*.lock")):
            try:
                data = json.loads(p.read_text())
                data["key"] = p.stem.replace("__", "/")
                data["expired"] = time.time() >= data.get("expires_at", 0)
                locks.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        return locks
