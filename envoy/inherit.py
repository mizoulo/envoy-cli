"""Env inheritance: merge a parent env into a child env with override semantics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.vault import Vault


@dataclass
class InheritResult:
    action: str
    parent: str
    child: str
    inherited: List[str] = field(default_factory=list)
    overridden: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"InheritResult(action={self.action!r}, parent={self.parent!r}, "
            f"child={self.child!r}, inherited={len(self.inherited)}, "
            f"overridden={len(self.overridden)}, success={self.success})"
        )


def _parse_env(text: str) -> Dict[str, str]:
    """Parse a .env-style string into a dict, ignoring comments and blanks."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def _serialize_env(pairs: Dict[str, str]) -> str:
    """Serialize a dict back to .env format."""
    return "\n".join(f"{k}={v}" for k, v in pairs.items())


def inherit_env(
    vault: Vault,
    project: str,
    parent_env: str,
    child_env: str,
    password: str,
) -> InheritResult:
    """Pull parent_env, merge into child_env (child keys take priority), push result."""
    try:
        parent_text = vault.pull(project, parent_env, password)
        parent_pairs = _parse_env(parent_text)
    except Exception as exc:
        return InheritResult(
            action="inherit", parent=parent_env, child=child_env,
            error=f"Failed to load parent '{parent_env}': {exc}",
        )

    try:
        child_text = vault.pull(project, child_env, password)
        child_pairs = _parse_env(child_text)
    except Exception:
        child_pairs = {}

    inherited: List[str] = []
    overridden: List[str] = []

    merged = dict(parent_pairs)
    for key, value in child_pairs.items():
        if key in merged:
            overridden.append(key)
        merged[key] = value

    for key in parent_pairs:
        if key not in child_pairs:
            inherited.append(key)

    try:
        vault.push(project, child_env, _serialize_env(merged), password)
    except Exception as exc:
        return InheritResult(
            action="inherit", parent=parent_env, child=child_env,
            error=f"Failed to push merged env: {exc}",
        )

    return InheritResult(
        action="inherit",
        parent=parent_env,
        child=child_env,
        inherited=inherited,
        overridden=overridden,
    )
