"""Access control for env entries — define read/write permissions per key pattern."""
from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class AccessRule:
    pattern: str
    permission: str  # "read", "write", "none"
    note: str = ""

    def matches(self, key: str) -> bool:
        return fnmatch.fnmatch(key, self.pattern)

    def to_dict(self) -> dict:
        return {"pattern": self.pattern, "permission": self.permission, "note": self.note}

    @classmethod
    def from_dict(cls, d: dict) -> "AccessRule":
        return cls(pattern=d["pattern"], permission=d["permission"], note=d.get("note", ""))


@dataclass
class AccessResult:
    allowed: bool
    key: str
    permission: str
    rule: Optional[AccessRule] = None
    error: str = ""

    def __bool__(self) -> bool:
        return self.allowed

    def __repr__(self) -> str:
        status = "allowed" if self.allowed else "denied"
        return f"<AccessResult {status} key={self.key!r} permission={self.permission!r}>"


class AccessManager:
    DEFAULT_PERMISSION = "write"

    def __init__(self, rules_path: Path) -> None:
        self.rules_path = rules_path
        self._rules: List[AccessRule] = self._load()

    def _load(self) -> List[AccessRule]:
        if not self.rules_path.exists():
            return []
        data = json.loads(self.rules_path.read_text())
        return [AccessRule.from_dict(r) for r in data.get("rules", [])]

    def _save(self) -> None:
        self.rules_path.write_text(
            json.dumps({"rules": [r.to_dict() for r in self._rules]}, indent=2)
        )

    def add_rule(self, pattern: str, permission: str, note: str = "") -> AccessRule:
        rule = AccessRule(pattern=pattern, permission=permission, note=note)
        self._rules.append(rule)
        self._save()
        return rule

    def remove_rule(self, pattern: str) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.pattern != pattern]
        if len(self._rules) < before:
            self._save()
            return True
        return False

    def check(self, key: str, action: str) -> AccessResult:
        """Check if `action` ('read' or 'write') is permitted for `key`."""
        for rule in reversed(self._rules):
            if rule.matches(key):
                allowed = rule.permission in (action, "write") if action == "read" else rule.permission == "write"
                return AccessResult(allowed=allowed, key=key, permission=action, rule=rule)
        return AccessResult(allowed=True, key=key, permission=action, rule=None)

    def list_rules(self) -> List[AccessRule]:
        return list(self._rules)
