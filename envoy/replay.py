"""Replay: re-apply a historical push/pull operation from audit log entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envoy.audit import AuditLog
from envoy.vault import Vault


@dataclass
class ReplayResult:
    action: str
    project: str
    env: str
    replayed: bool
    error: Optional[str] = None

    def success(self) -> bool:
        return self.replayed and self.error is None

    def __repr__(self) -> str:
        status = "ok" if self.success() else f"failed: {self.error}"
        return f"<ReplayResult {self.action} {self.project}/{self.env} [{status}]>"


@dataclass
class ReplayEngine:
    vault: Vault
    audit_log: AuditLog

    def last_entry(self, project: str, env: str, action: str) -> Optional[dict]:
        """Return the most recent audit entry matching project/env/action."""
        entries = [
            e for e in self.audit_log.all()
            if e.project == project and e.env == env and e.action == action
        ]
        if not entries:
            return None
        return entries[-1].to_dict()

    def replay_push(self, project: str, env: str, content: str, password: str) -> ReplayResult:
        """Re-push an env file content as if replaying a prior push."""
        try:
            self.vault.push(project, env, content, password)
            self.audit_log.record(action="replay_push", project=project, env=env)
            return ReplayResult(action="replay_push", project=project, env=env, replayed=True)
        except Exception as exc:  # noqa: BLE001
            return ReplayResult(
                action="replay_push", project=project, env=env,
                replayed=False, error=str(exc)
            )

    def replay_pull(self, project: str, env: str, password: str) -> ReplayResult:
        """Re-pull an env file, confirming the stored value is accessible."""
        try:
            content = self.vault.pull(project, env, password)
            if content is None:
                return ReplayResult(
                    action="replay_pull", project=project, env=env,
                    replayed=False, error="key not found"
                )
            self.audit_log.record(action="replay_pull", project=project, env=env)
            return ReplayResult(action="replay_pull", project=project, env=env, replayed=True)
        except Exception as exc:  # noqa: BLE001
            return ReplayResult(
                action="replay_pull", project=project, env=env,
                replayed=False, error=str(exc)
            )
