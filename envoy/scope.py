"""Scope management: restrict env access to named scopes (e.g. team, service)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envoy.vault import Vault


@dataclass
class ScopeResult:
    action: str
    scope: str
    ok: bool
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.ok

    def __repr__(self) -> str:
        status = "ok" if self.ok else f"error={self.error}"
        return f"<ScopeResult action={self.action} scope={self.scope} {status}>"


class ScopeManager:
    """Manages scoped push/pull operations by prefixing keys with a scope name."""

    def __init__(self, vault: Vault, scope: str) -> None:
        self.vault = vault
        self.scope = scope.strip("/")

    def _scoped_env(self, project: str, env: str) -> str:
        return f"{self.scope}/{env}"

    def push(self, project: str, env: str, content: str, password: str) -> ScopeResult:
        scoped = self._scoped_env(project, env)
        try:
            path = self.vault.push(project, scoped, content, password)
            return ScopeResult(action="push", scope=self.scope, ok=True)
        except Exception as exc:
            return ScopeResult(action="push", scope=self.scope, ok=False, error=str(exc))

    def pull(self, project: str, env: str, password: str) -> tuple[ScopeResult, Optional[str]]:
        scoped = self._scoped_env(project, env)
        try:
            content = self.vault.pull(project, scoped, password)
            return ScopeResult(action="pull", scope=self.scope, ok=True), content
        except Exception as exc:
            return ScopeResult(action="pull", scope=self.scope, ok=False, error=str(exc)), None

    def list_envs(self, project: str) -> List[str]:
        prefix = f"{self.scope}/"
        all_envs = self.vault.list_envs(project)
        return [e[len(prefix):] for e in all_envs if e.startswith(prefix)]

    def list_scopes(self, project: str) -> List[str]:
        all_envs = self.vault.list_envs(project)
        scopes = set()
        for e in all_envs:
            if "/" in e:
                scopes.add(e.split("/", 1)[0])
        return sorted(scopes)
