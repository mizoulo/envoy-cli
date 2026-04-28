"""Audit log for tracking push/pull operations on .env files."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    action: str  # 'push' | 'pull' | 'delete'
    env_name: str
    project: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user: Optional[str] = None
    details: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"[{self.timestamp}] {self.action.upper()} "
            f"{self.project}/{self.env_name}"
            + (f" — {self.details}" if self.details else "")
        )


class AuditLog:
    """Persists audit entries as newline-delimited JSON."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("", encoding="utf-8")

    def record(self, entry: AuditEntry) -> None:
        """Append a single audit entry to the log file."""
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")

    def entries(self, project: Optional[str] = None, action: Optional[str] = None) -> List[AuditEntry]:
        """Return all entries, optionally filtered by project or action."""
        results: List[AuditEntry] = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            entry = AuditEntry.from_dict(json.loads(line))
            if project and entry.project != project:
                continue
            if action and entry.action != action:
                continue
            results.append(entry)
        return results

    def clear(self) -> None:
        """Erase all audit log entries."""
        self.log_path.write_text("", encoding="utf-8")
