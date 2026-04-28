"""Diff utilities: compare a local .env file against a vault-stored version."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


def _parse_env(content: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines, ignoring comments and blank lines."""
    result: Dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


@dataclass
class EnvDiff:
    """Describes differences between two .env sources."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # key -> (old, new)

    @property
    def is_clean(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def summary_lines(self) -> List[str]:
        lines: List[str] = []
        for k, v in self.added.items():
            lines.append(f"+ {k}={v}")
        for k, v in self.removed.items():
            lines.append(f"- {k}={v}")
        for k, (old, new) in self.changed.items():
            lines.append(f"~ {k}: {old!r} -> {new!r}")
        return lines


def diff_env_strings(old_content: str, new_content: str) -> EnvDiff:
    """Return an EnvDiff comparing old_content (vault) to new_content (local)."""
    old = _parse_env(old_content)
    new = _parse_env(new_content)

    added = {k: v for k, v in new.items() if k not in old}
    removed = {k: v for k, v in old.items() if k not in new}
    changed = {
        k: (old[k], new[k])
        for k in old.keys() & new.keys()
        if old[k] != new[k]
    }
    return EnvDiff(added=added, removed=removed, changed=changed)


def diff_env_file_vs_bytes(local_path: Path, vault_bytes: bytes) -> EnvDiff:
    """Convenience wrapper: diff a local file against raw vault bytes."""
    local_content = local_path.read_text(encoding="utf-8") if local_path.exists() else ""
    vault_content = vault_bytes.decode("utf-8")
    return diff_env_strings(vault_content, local_content)
