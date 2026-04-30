"""Search and grep across .env files stored in the vault."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envoy.vault import Vault


@dataclass
class SearchMatch:
    project: str
    env_name: str
    line_number: int
    line: str

    def __repr__(self) -> str:
        return f"{self.project}/{self.env_name}:{self.line_number}: {self.line}"


@dataclass
class SearchResult:
    pattern: str
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return len(self.matches) > 0

    def summary(self) -> str:
        if not self.found:
            return f"No matches for '{self.pattern}'."
        return f"{len(self.matches)} match(es) for '{self.pattern}'."


class EnvSearcher:
    """Search for a pattern across all envs in a vault project."""

    def __init__(self, vault: Vault, password: str) -> None:
        self._vault = vault
        self._password = password

    def search(
        self,
        pattern: str,
        project: str,
        keys_only: bool = False,
        ignore_case: bool = False,
    ) -> SearchResult:
        """Return all lines matching *pattern* across every env in *project*."""
        flags = re.IGNORECASE if ignore_case else 0
        compiled = re.compile(pattern, flags)
        result = SearchResult(pattern=pattern)

        env_names = self._vault.list_envs(project)
        for env_name in env_names:
            try:
                content = self._vault.pull(project, env_name, self._password)
            except Exception:
                continue

            for lineno, raw_line in enumerate(content.splitlines(), start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                target = line.split("=", 1)[0] if keys_only else line
                if compiled.search(target):
                    result.matches.append(
                        SearchMatch(
                            project=project,
                            env_name=env_name,
                            line_number=lineno,
                            line=line,
                        )
                    )
        return result
