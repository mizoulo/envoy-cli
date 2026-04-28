"""Local and remote storage backends for .env file management."""

import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_STORE_DIR = Path.home() / ".envoy"
METADATA_FILE = "metadata.json"


class LocalStorage:
    """Manages encrypted .env file storage on the local filesystem."""

    def __init__(self, store_dir: Optional[Path] = None):
        self.store_dir = Path(store_dir) if store_dir else DEFAULT_STORE_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_path = self.store_dir / METADATA_FILE

    def _load_metadata(self) -> dict:
        if self._metadata_path.exists():
            with open(self._metadata_path, "r") as f:
                return json.load(f)
        return {}

    def _save_metadata(self, metadata: dict) -> None:
        with open(self._metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def save(self, project: str, env_name: str, ciphertext: str) -> Path:
        """Persist encrypted env data; returns the path written."""
        project_dir = self.store_dir / project
        project_dir.mkdir(parents=True, exist_ok=True)
        dest = project_dir / f"{env_name}.enc"
        dest.write_text(ciphertext)

        metadata = self._load_metadata()
        metadata.setdefault(project, {})[env_name] = str(dest)
        self._save_metadata(metadata)
        return dest

    def load(self, project: str, env_name: str) -> str:
        """Return the raw ciphertext for a stored env file."""
        dest = self.store_dir / project / f"{env_name}.enc"
        if not dest.exists():
            raise FileNotFoundError(
                f"No stored env '{env_name}' for project '{project}'"
            )
        return dest.read_text()

    def list_envs(self, project: str) -> list[str]:
        """List available env names for a given project."""
        metadata = self._load_metadata()
        return list(metadata.get(project, {}).keys())

    def delete(self, project: str, env_name: str) -> None:
        """Remove a stored env file and update metadata."""
        dest = self.store_dir / project / f"{env_name}.enc"
        if dest.exists():
            dest.unlink()
        metadata = self._load_metadata()
        if project in metadata and env_name in metadata[project]:
            del metadata[project][env_name]
            if not metadata[project]:
                del metadata[project]
            self._save_metadata(metadata)
