"""HMAC-based signing and verification for .env file integrity."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SignResult:
    action: str
    key: str
    ok: bool
    error: Optional[str] = None

    def success(self) -> bool:
        return self.ok

    def __repr__(self) -> str:
        status = "ok" if self.ok else f"error={self.error}"
        return f"SignResult(action={self.action!r}, key={self.key!r}, {status})"


def _compute_hmac(data: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()


class SignatureStore:
    """Persist and verify HMAC signatures for stored env blobs."""

    def __init__(self, store_path: Path) -> None:
        self._path = store_path
        self._index: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._index, indent=2))

    def sign(self, key: str, data: bytes, secret: str) -> SignResult:
        try:
            digest = _compute_hmac(data, secret)
            self._index[key] = digest
            self._save()
            return SignResult(action="sign", key=key, ok=True)
        except Exception as exc:  # pragma: no cover
            return SignResult(action="sign", key=key, ok=False, error=str(exc))

    def verify(self, key: str, data: bytes, secret: str) -> SignResult:
        stored = self._index.get(key)
        if stored is None:
            return SignResult(action="verify", key=key, ok=False, error="no signature found")
        expected = _compute_hmac(data, secret)
        if hmac.compare_digest(stored, expected):
            return SignResult(action="verify", key=key, ok=True)
        return SignResult(action="verify", key=key, ok=False, error="signature mismatch")

    def remove(self, key: str) -> SignResult:
        if key not in self._index:
            return SignResult(action="remove", key=key, ok=False, error="key not found")
        del self._index[key]
        self._save()
        return SignResult(action="remove", key=key, ok=True)

    def list_keys(self) -> list[str]:
        return list(self._index.keys())
