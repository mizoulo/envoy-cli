"""Pin management: lock a project/env to a specific snapshot revision."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class PinResult:
    project: str
    env: str
    snapshot_key: Optional[str]
    action: str  # 'pinned', 'unpinned', 'already_pinned', 'not_found'

    @property
    def success(self) -> bool:
        return self.action in ("pinned", "unpinned")

    def __repr__(self) -> str:
        return f"<PinResult {self.action} {self.project}/{self.env} -> {self.snapshot_key}>"


class PinManager:
    """Persist and query snapshot pins stored in a JSON file."""

    def __init__(self, store_path: Path) -> None:
        self._path = Path(store_path)
        self._pins: Dict[str, str] = self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, str]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._pins, indent=2))

    @staticmethod
    def _key(project: str, env: str) -> str:
        return f"{project}/{env}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def pin(self, project: str, env: str, snapshot_key: str) -> PinResult:
        """Pin *project/env* to *snapshot_key*."""
        k = self._key(project, env)
        if self._pins.get(k) == snapshot_key:
            return PinResult(project, env, snapshot_key, "already_pinned")
        self._pins[k] = snapshot_key
        self._save()
        return PinResult(project, env, snapshot_key, "pinned")

    def unpin(self, project: str, env: str) -> PinResult:
        """Remove any pin for *project/env*."""
        k = self._key(project, env)
        if k not in self._pins:
            return PinResult(project, env, None, "not_found")
        del self._pins[k]
        self._save()
        return PinResult(project, env, None, "unpinned")

    def get_pin(self, project: str, env: str) -> Optional[str]:
        """Return the pinned snapshot key, or *None* if not pinned."""
        return self._pins.get(self._key(project, env))

    def list_pins(self, project: Optional[str] = None) -> Dict[str, str]:
        """Return all pins, optionally filtered by *project*."""
        if project is None:
            return dict(self._pins)
        prefix = f"{project}/"
        return {k: v for k, v in self._pins.items() if k.startswith(prefix)}
