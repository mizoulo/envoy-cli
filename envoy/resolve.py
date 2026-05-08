"""Variable resolution: expand ${VAR} references within .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass
class ResolveResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    unresolved: List[str] = field(default_factory=list)
    cycles: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and not self.cycles

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ResolveResult(resolved={len(self.resolved)}, "
            f"unresolved={self.unresolved}, cycles={self.cycles})"
        )


def _parse_env(text: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _expand(key: str, env: Dict[str, str], cache: Dict[str, str], visiting: set) -> str:
    if key in cache:
        return cache[key]
    if key not in env:
        return ""  # unresolvable reference
    if key in visiting:
        raise RecursionError(key)
    visiting.add(key)
    value = env[key]
    def _sub(m: re.Match) -> str:
        ref = m.group(1)
        return _expand(ref, env, cache, visiting)
    result = _REF_RE.sub(_sub, value)
    visiting.discard(key)
    cache[key] = result
    return result


def resolve_env(text: str) -> ResolveResult:
    """Parse *text* as a .env file and expand all ${VAR} references."""
    env = _parse_env(text)
    cache: Dict[str, str] = {}
    unresolved: List[str] = []
    cycles: List[str] = []

    for key in env:
        try:
            _expand(key, env, cache, set())
        except RecursionError as exc:
            cycles.append(str(exc))

    resolved: Dict[str, str] = {}
    for key in env:
        if key in cycles:
            continue
        value = cache.get(key, env[key])
        refs = _REF_RE.findall(env[key])
        missing = [r for r in refs if r not in env]
        if missing:
            unresolved.append(key)
        resolved[key] = value

    return ResolveResult(resolved=resolved, unresolved=unresolved, cycles=cycles)
