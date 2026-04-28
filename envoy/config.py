"""Configuration management for envoy-cli."""

import json
import os
from pathlib import Path
from typing import Any, Optional

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "envoy"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "storage_path": str(Path.home() / ".local" / "share" / "envoy" / "vault"),
    "default_project": None,
    "auto_sync": False,
    "encryption_iterations": 600_000,
}


class Config:
    """Manages envoy-cli configuration stored as JSON."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load config from disk, falling back to defaults."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                stored = json.load(f)
            self._data = {**DEFAULT_CONFIG, **stored}
        else:
            self._data = dict(DEFAULT_CONFIG)

    def save(self) -> None:
        """Persist current config to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a config value by key."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value and persist to disk."""
        self._data[key] = value
        self.save()

    def reset(self) -> None:
        """Reset all config values to defaults."""
        self._data = dict(DEFAULT_CONFIG)
        self.save()

    def as_dict(self) -> dict[str, Any]:
        """Return a copy of the current configuration."""
        return dict(self._data)

    def __repr__(self) -> str:
        return f"Config(path={self.config_path}, data={self._data})"
