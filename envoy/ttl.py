"""TTL (time-to-live) management for stored env entries."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from envoy.storage import LocalStorage


@dataclass
class TTLResult:
    action: str
    key: str
    error: Optional[str] = None

    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:
        status = "ok" if self.success() else f"error={self.error}"
        return f"<TTLResult action={self.action} key={self.key} {status}>"


class TTLManager:
    _META_KEY = "ttl_expiry"

    def __init__(self, storage: LocalStorage) -> None:
        self._storage = storage

    def set_ttl(self, project: str, env: str, seconds: int) -> TTLResult:
        key = f"{project}/{env}"
        try:
            expiry = time.time() + seconds
            meta = self._storage._load_metadata()
            ttl_map = meta.setdefault(self._META_KEY, {})
            ttl_map[key] = expiry
            self._storage._save_metadata(meta)
            return TTLResult(action="set", key=key)
        except Exception as exc:  # pragma: no cover
            return TTLResult(action="set", key=key, error=str(exc))

    def get_expiry(self, project: str, env: str) -> Optional[float]:
        key = f"{project}/{env}"
        meta = self._storage._load_metadata()
        return meta.get(self._META_KEY, {}).get(key)

    def is_expired(self, project: str, env: str) -> bool:
        expiry = self.get_expiry(project, env)
        if expiry is None:
            return False
        return time.time() > expiry

    def clear_ttl(self, project: str, env: str) -> TTLResult:
        key = f"{project}/{env}"
        try:
            meta = self._storage._load_metadata()
            meta.get(self._META_KEY, {}).pop(key, None)
            self._storage._save_metadata(meta)
            return TTLResult(action="clear", key=key)
        except Exception as exc:  # pragma: no cover
            return TTLResult(action="clear", key=key, error=str(exc))

    def list_expiring(self) -> list[dict]:
        meta = self._storage._load_metadata()
        ttl_map = meta.get(self._META_KEY, {})
        now = time.time()
        entries = []
        for key, expiry in ttl_map.items():
            entries.append({
                "key": key,
                "expiry": expiry,
                "expired": now > expiry,
                "remaining": max(0.0, expiry - now),
            })
        return entries
