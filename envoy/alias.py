"""Alias management for env keys — rename keys across a stored env."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.vault import Vault


@dataclass
class AliasResult:
    action: str
    original: str
    alias: str
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:  # pragma: no cover
        status = "ok" if self.success else f"error={self.error!r}"
        return f"AliasResult(action={self.action!r}, {self.original!r}->{self.alias!r}, {status})"


class AliasManager:
    """Add, remove, and apply key aliases for a project/env pair."""

    def __init__(self, vault: Vault, project: str, env: str) -> None:
        self._vault = vault
        self._project = project
        self._env = env
        self._alias_key = f"{project}/{env}/__aliases__"

    def _load_aliases(self) -> Dict[str, str]:
        """Return {alias: original} mapping stored in the vault."""
        try:
            raw = self._vault.pull(self._project, self._alias_key)
        except KeyError:
            return {}
        aliases: Dict[str, str] = {}
        for line in raw.splitlines():
            if "=" in line:
                alias, original = line.split("=", 1)
                aliases[alias.strip()] = original.strip()
        return aliases

    def _save_aliases(self, aliases: Dict[str, str]) -> None:
        content = "\n".join(f"{a}={o}" for a, o in sorted(aliases.items()))
        self._vault.push(self._project, self._alias_key, content)

    def add(self, original: str, alias: str) -> AliasResult:
        """Register *alias* as an alternative name for *original*."""
        aliases = self._load_aliases()
        if alias in aliases:
            return AliasResult("add", original, alias, error=f"alias {alias!r} already exists")
        aliases[alias] = original
        self._save_aliases(aliases)
        return AliasResult("add", original, alias)

    def remove(self, alias: str) -> AliasResult:
        """Unregister an alias."""
        aliases = self._load_aliases()
        original = aliases.pop(alias, None)
        if original is None:
            return AliasResult("remove", "", alias, error=f"alias {alias!r} not found")
        self._save_aliases(aliases)
        return AliasResult("remove", original, alias)

    def list_aliases(self) -> Dict[str, str]:
        """Return all registered aliases as {alias: original}."""
        return self._load_aliases()

    def resolve(self, name: str) -> str:
        """Return the original key name for *name*, or *name* itself if not aliased."""
        return self._load_aliases().get(name, name)

    def apply(self, env_content: str) -> str:
        """Rewrite *env_content* replacing original keys with their aliases."""
        aliases = self._load_aliases()
        # invert: original -> alias
        original_to_alias = {v: k for k, v in aliases.items()}
        lines: List[str] = []
        for line in env_content.splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                key = original_to_alias.get(key.strip(), key.strip())
                lines.append(f"{key}={value}")
            else:
                lines.append(line)
        return "\n".join(lines)
