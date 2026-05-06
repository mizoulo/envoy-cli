"""Prune stale or expired env entries from a vault project."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from envoy.vault import Vault


@dataclass
class PruneResult:
    removed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PruneResult(removed={len(self.removed)}, "
            f"skipped={len(self.skipped)}, success={self.success})"
        )


def _is_expired(metadata: dict, cutoff: datetime) -> bool:
    """Return True when the entry's timestamp is older than *cutoff*."""
    ts = metadata.get("updated_at") or metadata.get("created_at")
    if not ts:
        return False
    try:
        entry_time = datetime.fromisoformat(ts)
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=timezone.utc)
        return entry_time < cutoff
    except ValueError:
        return False


def prune_project(
    vault: Vault,
    project: str,
    *,
    before: Optional[datetime] = None,
    dry_run: bool = False,
) -> PruneResult:
    """Remove env entries for *project* that are older than *before*.

    When *dry_run* is ``True`` the entries are identified but not deleted.
    If *before* is ``None`` every entry for the project is considered stale.
    """
    result = PruneResult()
    try:
        envs = vault.list_envs(project)
    except Exception as exc:  # noqa: BLE001
        result.error = str(exc)
        return result

    for env_name in envs:
        try:
            meta = vault.storage.get_metadata(project, env_name)
            if before is not None and not _is_expired(meta, before):
                result.skipped.append(env_name)
                continue
            if not dry_run:
                vault.storage.delete(project, env_name)
            result.removed.append(env_name)
        except Exception as exc:  # noqa: BLE001
            result.skipped.append(env_name)
            result.error = str(exc)

    return result
