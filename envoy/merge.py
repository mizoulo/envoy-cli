"""Merge two .env files with configurable conflict resolution strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ConflictStrategy(str, Enum):
    OURS = "ours"       # keep value from base
    THEIRS = "theirs"   # take value from other
    ERROR = "error"     # raise on conflict


@dataclass
class MergeConflict:
    key: str
    base_value: str
    other_value: str

    def __repr__(self) -> str:
        return f"MergeConflict(key={self.key!r}, base={self.base_value!r}, other={self.other_value!r})"


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: List[MergeConflict] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.conflicts) == 0

    def to_env_string(self) -> str:
        lines = [f"{k}={v}" for k, v in sorted(self.merged.items())]
        return "\n".join(lines) + ("\n" if lines else "")

    def summary(self) -> str:
        parts = [f"{len(self.merged)} keys in result"]
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.overwritten:
            parts.append(f"{len(self.overwritten)} overwritten")
        if self.conflicts:
            parts.append(f"{len(self.conflicts)} conflict(s)")
        return ", ".join(parts)


def _parse_env(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def merge_envs(
    base: str,
    other: str,
    strategy: ConflictStrategy = ConflictStrategy.OURS,
) -> MergeResult:
    """Merge *other* into *base* using the given conflict strategy."""
    base_map = _parse_env(base)
    other_map = _parse_env(other)

    merged: Dict[str, str] = dict(base_map)
    conflicts: List[MergeConflict] = []
    added: List[str] = []
    overwritten: List[str] = []

    for key, other_val in other_map.items():
        if key not in base_map:
            merged[key] = other_val
            added.append(key)
        elif base_map[key] != other_val:
            conflict = MergeConflict(key, base_map[key], other_val)
            if strategy == ConflictStrategy.ERROR:
                conflicts.append(conflict)
            elif strategy == ConflictStrategy.THEIRS:
                merged[key] = other_val
                overwritten.append(key)
            # OURS: keep base value — no change needed

    return MergeResult(merged=merged, conflicts=conflicts, added=added, overwritten=overwritten)
