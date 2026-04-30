"""File watcher that triggers sync when .env files change."""

from __future__ import annotations

import time
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class WatchEvent:
    path: Path
    project: str
    env_name: str
    old_hash: Optional[str]
    new_hash: str

    def __repr__(self) -> str:
        action = "created" if self.old_hash is None else "modified"
        return f"<WatchEvent {action} {self.project}/{self.env_name}>"


def _file_hash(path: Path) -> Optional[str]:
    """Return SHA256 hex digest of file contents, or None if missing."""
    try:
        data = path.read_bytes()
        return hashlib.sha256(data).hexdigest()
    except FileNotFoundError:
        return None


class EnvWatcher:
    """Poll watched .env files and invoke a callback on changes."""

    def __init__(self, interval: float = 1.0) -> None:
        self.interval = interval
        self._watched: Dict[Path, Dict] = {}  # path -> {project, env_name, last_hash}
        self._callbacks: List[Callable[[WatchEvent], None]] = []

    def add(self, path: Path, project: str, env_name: str) -> None:
        """Register a file to watch."""
        self._watched[path] = {
            "project": project,
            "env_name": env_name,
            "last_hash": _file_hash(path),
        }

    def on_change(self, callback: Callable[[WatchEvent], None]) -> None:
        """Register a callback invoked with a WatchEvent on file change."""
        self._callbacks.append(callback)

    def check_once(self) -> List[WatchEvent]:
        """Check all watched files for changes; return list of events."""
        events: List[WatchEvent] = []
        for path, meta in self._watched.items():
            current = _file_hash(path)
            if current != meta["last_hash"]:
                event = WatchEvent(
                    path=path,
                    project=meta["project"],
                    env_name=meta["env_name"],
                    old_hash=meta["last_hash"],
                    new_hash=current,
                )
                meta["last_hash"] = current
                events.append(event)
                for cb in self._callbacks:
                    cb(event)
        return events

    def run(self, max_iterations: Optional[int] = None) -> None:
        """Block and poll indefinitely (or up to max_iterations for testing)."""
        iterations = 0
        while True:
            self.check_once()
            time.sleep(self.interval)
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
