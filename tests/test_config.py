"""Tests for envoy.config module."""

import json
import pytest
from pathlib import Path

from envoy.config import Config, DEFAULT_CONFIG


@pytest.fixture
def config(tmp_path: Path) -> Config:
    config_file = tmp_path / "config.json"
    return Config(config_path=config_file)


def test_default_values_loaded(config: Config) -> None:
    for key, value in DEFAULT_CONFIG.items():
        assert config.get(key) == value


def test_get_missing_key_returns_default(config: Config) -> None:
    assert config.get("nonexistent_key", "fallback") == "fallback"


def test_set_persists_value(config: Config, tmp_path: Path) -> None:
    config.set("auto_sync", True)
    assert config.get("auto_sync") is True

    reloaded = Config(config_path=config.config_path)
    assert reloaded.get("auto_sync") is True


def test_save_creates_file(config: Config) -> None:
    config.save()
    assert config.config_path.exists()


def test_save_writes_valid_json(config: Config) -> None:
    config.save()
    with open(config.config_path, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert "storage_path" in data


def test_reset_restores_defaults(config: Config) -> None:
    config.set("auto_sync", True)
    config.set("default_project", "my-project")
    config.reset()

    assert config.get("auto_sync") == DEFAULT_CONFIG["auto_sync"]
    assert config.get("default_project") == DEFAULT_CONFIG["default_project"]


def test_as_dict_returns_copy(config: Config) -> None:
    d = config.as_dict()
    d["auto_sync"] = True
    assert config.get("auto_sync") == DEFAULT_CONFIG["auto_sync"]


def test_load_merges_with_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"auto_sync": True}))

    cfg = Config(config_path=config_file)
    assert cfg.get("auto_sync") is True
    assert cfg.get("storage_path") == DEFAULT_CONFIG["storage_path"]


def test_repr_contains_path(config: Config) -> None:
    assert str(config.config_path) in repr(config)
