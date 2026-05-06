"""Backup and restore .env files to/from a local archive directory."""
from __future__ import annotations

import shutil
import tarfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class BackupResult:
    action: str
    archive: Optional[Path] = None
    restored_to: Optional[Path] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:  # pragma: no cover
        status = "ok" if self.success else f"error={self.error}"
        return f"<BackupResult action={self.action} {status}>"


class BackupManager:
    """Create and restore timestamped .tar.gz backups of env files."""

    def __init__(self, backup_dir: Path) -> None:
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _timestamp(self) -> str:
        return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def create(
        self,
        sources: List[Path],
        label: Optional[str] = None,
    ) -> BackupResult:
        """Archive *sources* into a single .tar.gz file."""
        tag = f"{label}-" if label else ""
        archive_name = f"envoy-backup-{tag}{self._timestamp()}.tar.gz"
        archive_path = self.backup_dir / archive_name
        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                for src in sources:
                    if not src.exists():
                        return BackupResult(
                            action="create",
                            error=f"source not found: {src}",
                        )
                    tar.add(src, arcname=src.name)
        except Exception as exc:  # pragma: no cover
            return BackupResult(action="create", error=str(exc))
        return BackupResult(action="create", archive=archive_path)

    def restore(self, archive: Path, target_dir: Path) -> BackupResult:
        """Extract *archive* into *target_dir*."""
        if not archive.exists():
            return BackupResult(action="restore", error=f"archive not found: {archive}")
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(target_dir)
        except Exception as exc:  # pragma: no cover
            return BackupResult(action="restore", error=str(exc))
        return BackupResult(action="restore", archive=archive, restored_to=target_dir)

    def list_backups(self) -> List[Path]:
        """Return sorted list of backup archives (oldest first)."""
        return sorted(self.backup_dir.glob("envoy-backup-*.tar.gz"))

    def prune(self, keep: int = 5) -> List[Path]:
        """Delete oldest backups, keeping the *keep* most recent."""
        archives = self.list_backups()
        to_delete = archives[: max(0, len(archives) - keep)]
        for path in to_delete:
            path.unlink()
        return to_delete
