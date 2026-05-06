"""Track push/pull history for env files per project."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class HistoryEntry:
    action: str          # 'push' | 'pull'
    project: str
    env_name: str
    timestamp: str
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "project": self.project,
            "env_name": self.env_name,
            "timestamp": self.timestamp,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            action=data["action"],
            project=data["project"],
            env_name=data["env_name"],
            timestamp=data["timestamp"],
            note=data.get("note"),
        )

    def __repr__(self) -> str:
        note_part = f" ({self.note})" if self.note else ""
        return (
            f"<HistoryEntry {self.action} {self.project}/{self.env_name} "
            f"at {self.timestamp}{note_part}>"
        )


class HistoryLog:
    def __init__(self, history_path: Path) -> None:
        self._path = history_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text(json.dumps([]), encoding="utf-8")

    def _load(self) -> List[dict]:
        return json.loads(self._path.read_text(encoding="utf-8"))

    def record(self, action: str, project: str, env_name: str, note: Optional[str] = None) -> HistoryEntry:
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = HistoryEntry(action=action, project=project, env_name=env_name,
                             timestamp=timestamp, note=note)
        entries = self._load()
        entries.append(entry.to_dict())
        self._path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        return entry

    def all(self) -> List[HistoryEntry]:
        return [HistoryEntry.from_dict(d) for d in self._load()]

    def filter(self, project: Optional[str] = None, action: Optional[str] = None) -> List[HistoryEntry]:
        entries = self.all()
        if project:
            entries = [e for e in entries if e.project == project]
        if action:
            entries = [e for e in entries if e.action == action]
        return entries

    def clear(self, project: Optional[str] = None) -> int:
        if project is None:
            removed = len(self._load())
            self._path.write_text(json.dumps([]), encoding="utf-8")
            return removed
        before = self._load()
        after = [d for d in before if d["project"] != project]
        self._path.write_text(json.dumps(after, indent=2), encoding="utf-8")
        return len(before) - len(after)
