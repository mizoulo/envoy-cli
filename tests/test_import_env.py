"""Tests for envoy/import_env.py."""
import json
import pytest
from pathlib import Path

from envoy.import_env import (
    ImportResult,
    _parse_dotenv,
    _parse_json,
    _parse_shell,
    import_env,
)


# ---------------------------------------------------------------------------
# Unit tests for parsers
# ---------------------------------------------------------------------------

def test_parse_dotenv_basic():
    text = "KEY=value\nOTHER=123\n"
    assert _parse_dotenv(text) == {"KEY": "value", "OTHER": "123"}


def test_parse_dotenv_ignores_comments_and_blanks():
    text = "# comment\n\nKEY=val\n"
    assert _parse_dotenv(text) == {"KEY": "val"}


def test_parse_dotenv_strips_quotes():
    text = 'KEY="quoted value"\nOTHER=\'single\'\n'
    assert _parse_dotenv(text) == {"KEY": "quoted value", "OTHER": "single"}


def test_parse_json_basic():
    data = json.dumps({"A": "1", "B": "hello"})
    assert _parse_json(data) == {"A": "1", "B": "hello"}


def test_parse_json_non_dict_raises():
    with pytest.raises(ValueError, match="JSON root must be an object"):
        _parse_json(json.dumps(["a", "b"]))


def test_parse_shell_basic():
    text = "export KEY=value\nexport OTHER=123\n"
    assert _parse_shell(text) == {"KEY": "value", "OTHER": "123"}


def test_parse_shell_without_export_prefix():
    text = "KEY=value\n"
    assert _parse_shell(text) == {"KEY": "value"}


# ---------------------------------------------------------------------------
# Integration tests for import_env()
# ---------------------------------------------------------------------------

def test_import_env_dotenv(tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("DB=postgres\nSECRET=abc\n")
    pairs, result = import_env(str(f), fmt="dotenv")
    assert pairs == {"DB": "postgres", "SECRET": "abc"}
    assert result.imported == 2
    assert result.skipped == 0
    assert result.success


def test_import_env_json(tmp_path: Path):
    f = tmp_path / "env.json"
    f.write_text(json.dumps({"X": "1", "Y": "2"}))
    pairs, result = import_env(str(f), fmt="json")
    assert pairs == {"X": "1", "Y": "2"}
    assert result.fmt == "json"


def test_import_env_skip_existing(tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("A=1\nB=2\nC=3\n")
    pairs, result = import_env(str(f), skip_existing=True, existing_keys=["A", "C"])
    assert "A" not in pairs
    assert "C" not in pairs
    assert pairs == {"B": "2"}
    assert result.skipped == 2
    assert result.imported == 1


def test_import_env_unknown_format_raises(tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("K=V")
    with pytest.raises(ValueError, match="Unknown format"):
        import_env(str(f), fmt="toml")


def test_import_result_repr():
    r = ImportResult(source="x.env", fmt="dotenv", imported=3, skipped=1)
    assert "dotenv" in repr(r)
    assert "imported=3" in repr(r)
