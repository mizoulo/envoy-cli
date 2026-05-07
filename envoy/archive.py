"""Archive module: compress and bundle multiple env entries into a single archive file."""
from __future__ import annotations

import json
import zipfile
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ArchiveResult:
    action: str
    path: Optional[str] = None
    entries: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:
        status = "ok" if self.success else f"error={self.error}"
        return f"<ArchiveResult action={self.action} entries={len(self.entries)} {status}>"


class ArchiveManager:
    """Create and extract zip archives of env blobs from a vault."""

    def __init__(self, vault) -> None:
        self._vault = vault

    def create(self, project: str, dest: Path, password: str) -> ArchiveResult:
        """Bundle all env entries for *project* into a zip archive at *dest*."""
        try:
            keys = self._vault.list_envs(project)
            if not keys:
                return ArchiveResult(action="create", error=f"no entries found for project '{project}'")

            dest = Path(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                manifest: Dict[str, str] = {}
                for env_name in keys:
                    content = self._vault.pull(project, env_name, password)
                    zf.writestr(f"{env_name}.env", content)
                    manifest[env_name] = f"{env_name}.env"
                zf.writestr("manifest.json", json.dumps(manifest, indent=2))

            return ArchiveResult(action="create", path=str(dest), entries=list(keys))
        except Exception as exc:  # noqa: BLE001
            return ArchiveResult(action="create", error=str(exc))

    def extract(self, project: str, src: Path, password: str) -> ArchiveResult:
        """Restore env entries from *src* archive back into the vault."""
        try:
            src = Path(src)
            if not src.exists():
                return ArchiveResult(action="extract", error=f"archive not found: {src}")

            restored: List[str] = []
            with zipfile.ZipFile(src, "r") as zf:
                raw = zf.read("manifest.json")
                manifest: Dict[str, str] = json.loads(raw)
                for env_name, member in manifest.items():
                    content = zf.read(member).decode()
                    self._vault.push(project, env_name, content, password)
                    restored.append(env_name)

            return ArchiveResult(action="extract", path=str(src), entries=restored)
        except Exception as exc:  # noqa: BLE001
            return ArchiveResult(action="extract", error=str(exc))
