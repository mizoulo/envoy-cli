"""Checksum utilities for verifying .env file integrity."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class ChecksumResult:
    key: str
    expected: Optional[str]
    actual: Optional[str]
    matched: bool

    def __repr__(self) -> str:  # pragma: no cover
        status = "OK" if self.matched else "MISMATCH"
        return f"<ChecksumResult key={self.key!r} status={status}>"


def _compute(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ChecksumStore:
    """Persist and verify SHA-256 checksums for stored env blobs."""

    def __init__(self, store_path: Path) -> None:
        self._path = store_path
        self._checksums: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._checksums, indent=2))

    def record(self, key: str, data: bytes) -> str:
        """Compute and store the checksum for *key*. Returns the hex digest."""
        digest = _compute(data)
        self._checksums[key] = digest
        self._save()
        return digest

    def verify(self, key: str, data: bytes) -> ChecksumResult:
        """Verify *data* against the stored checksum for *key*."""
        expected = self._checksums.get(key)
        actual = _compute(data)
        matched = expected is not None and expected == actual
        return ChecksumResult(key=key, expected=expected, actual=actual, matched=matched)

    def remove(self, key: str) -> bool:
        """Delete the stored checksum for *key*. Returns True if it existed."""
        if key in self._checksums:
            del self._checksums[key]
            self._save()
            return True
        return False

    def all_keys(self) -> list:
        return list(self._checksums.keys())
