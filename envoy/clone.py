"""Clone an environment from one project/namespace to another."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envoy.vault import Vault


@dataclass
class CloneResult:
    action: str
    source_project: str
    source_env: str
    dest_project: str
    dest_env: str
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:  # pragma: no cover
        status = "ok" if self.success else f"error={self.error}"
        return (
            f"CloneResult(action={self.action!r}, "
            f"{self.source_project!r}/{self.source_env!r} -> "
            f"{self.dest_project!r}/{self.dest_env!r}, {status})"
        )


def clone_env(
    vault: Vault,
    source_project: str,
    source_env: str,
    dest_project: str,
    dest_env: str,
    overwrite: bool = False,
) -> CloneResult:
    """Copy an encrypted env from *source* to *dest* within the same vault."""
    action = "clone"

    # Check source exists
    available = vault.list_envs(source_project)
    if source_env not in available:
        return CloneResult(
            action=action,
            source_project=source_project,
            source_env=source_env,
            dest_project=dest_project,
            dest_env=dest_env,
            error=f"source env '{source_env}' not found in project '{source_project}'",
        )

    # Guard against accidental overwrite
    if not overwrite and dest_env in vault.list_envs(dest_project):
        return CloneResult(
            action=action,
            source_project=source_project,
            source_env=source_env,
            dest_project=dest_project,
            dest_env=dest_env,
            error=(
                f"destination env '{dest_env}' already exists in project "
                f"'{dest_project}'. Use overwrite=True to replace it."
            ),
        )

    try:
        plaintext = vault.pull(source_project, source_env)
        vault.push(dest_project, dest_env, plaintext)
    except Exception as exc:  # noqa: BLE001
        return CloneResult(
            action=action,
            source_project=source_project,
            source_env=source_env,
            dest_project=dest_project,
            dest_env=dest_env,
            error=str(exc),
        )

    return CloneResult(
        action=action,
        source_project=source_project,
        source_env=source_env,
        dest_project=dest_project,
        dest_env=dest_env,
    )
