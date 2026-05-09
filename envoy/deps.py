"""Dependency tracking for .env files — detect when one env references keys from another."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

_REF_RE = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}|\$([A-Z_][A-Z0-9_]*)")


def _parse_env(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def _extract_refs(value: str) -> Set[str]:
    refs: Set[str] = set()
    for m in _REF_RE.finditer(value):
        refs.add(m.group(1) or m.group(2))
    return refs


@dataclass
class DepResult:
    source: str
    missing: List[str] = field(default_factory=list)
    satisfied: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and not self.missing

    def __repr__(self) -> str:
        return (
            f"DepResult(source={self.source!r}, "
            f"missing={self.missing}, satisfied={self.satisfied})"
        )


@dataclass
class DepGraph:
    """Stores a dependency index mapping env file paths to their referenced keys."""
    _index_path: Path
    _graph: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self._index_path.exists():
            raw = json.loads(self._index_path.read_text())
            self._graph = raw

    def _save(self) -> None:
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._index_path.write_text(json.dumps(self._graph, indent=2))

    def record(self, env_path: str, env_text: str) -> None:
        """Index all external references found in env_text for env_path."""
        parsed = _parse_env(env_text)
        defined = set(parsed.keys())
        refs: Set[str] = set()
        for value in parsed.values():
            refs |= _extract_refs(value)
        external = sorted(refs - defined)
        self._graph[env_path] = external
        self._save()

    def check(self, env_path: str, provider_text: str) -> DepResult:
        """Check whether provider_text satisfies all external refs of env_path."""
        required = set(self._graph.get(env_path, []))
        provided = set(_parse_env(provider_text).keys())
        missing = sorted(required - provided)
        satisfied = sorted(required & provided)
        return DepResult(source=env_path, missing=missing, satisfied=satisfied)

    def all_deps(self) -> Dict[str, List[str]]:
        return dict(self._graph)
