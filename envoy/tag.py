"""Tag management for .env files stored in the vault."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


@dataclass
class TagResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:
        return (
            f"TagResult(added={len(self.added)}, "
            f"removed={len(self.removed)}, errors={len(self.errors)})"
        )


class TagManager:
    """Manages tags associated with vault entries."""

    TAG_NAMESPACE = "__tags__"

    def __init__(self, vault) -> None:
        self._vault = vault

    def _tag_key(self, project: str, env: str) -> str:
        return f"{self.TAG_NAMESPACE}/{project}/{env}"

    def _load_tags(self, project: str, env: str) -> List[str]:
        key = self._tag_key(project, env)
        try:
            raw = self._vault.pull(project, key)
            return json.loads(raw)
        except Exception:
            return []

    def _save_tags(self, project: str, env: str, tags: List[str]) -> None:
        key = self._tag_key(project, env)
        self._vault.push(project, key, json.dumps(sorted(set(tags))))

    def add(self, project: str, env: str, tags: List[str]) -> TagResult:
        result = TagResult()
        current = self._load_tags(project, env)
        new_tags = [t for t in tags if t not in current]
        if new_tags:
            try:
                self._save_tags(project, env, current + new_tags)
                result.added.extend(new_tags)
            except Exception as exc:
                result.errors.append(str(exc))
        return result

    def remove(self, project: str, env: str, tags: List[str]) -> TagResult:
        result = TagResult()
        current = self._load_tags(project, env)
        kept = [t for t in current if t not in tags]
        removed = [t for t in tags if t in current]
        if removed:
            try:
                self._save_tags(project, env, kept)
                result.removed.extend(removed)
            except Exception as exc:
                result.errors.append(str(exc))
        return result

    def list_tags(self, project: str, env: str) -> List[str]:
        return self._load_tags(project, env)

    def find_by_tag(self, project: str, tag: str) -> List[str]:
        """Return env names in a project that carry the given tag."""
        matches = []
        for env in self._vault.list_envs(project):
            if tag in self._load_tags(project, env):
                matches.append(env)
        return matches
