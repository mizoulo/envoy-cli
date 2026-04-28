"""Tests for envoy.diff utilities."""

from __future__ import annotations

from pathlib import Path
import pytest

from envoy.diff import diff_env_strings, diff_env_file_vs_bytes, EnvDiff, _parse_env


def test_parse_env_basic():
    content = "DB=postgres\nSECRET=abc\n"
    result = _parse_env(content)
    assert result == {"DB": "postgres", "SECRET": "abc"}


def test_parse_env_ignores_comments_and_blanks():
    content = "# comment\n\nKEY=val\n"
    assert _parse_env(content) == {"KEY": "val"}


def test_diff_no_changes():
    content = "A=1\nB=2"
    d = diff_env_strings(content, content)
    assert d.is_clean


def test_diff_added_key():
    old = "A=1"
    new = "A=1\nB=2"
    d = diff_env_strings(old, new)
    assert "B" in d.added
    assert not d.removed
    assert not d.changed


def test_diff_removed_key():
    old = "A=1\nB=2"
    new = "A=1"
    d = diff_env_strings(old, new)
    assert "B" in d.removed
    assert not d.added


def test_diff_changed_key():
    old = "A=old_value"
    new = "A=new_value"
    d = diff_env_strings(old, new)
    assert "A" in d.changed
    assert d.changed["A"] == ("old_value", "new_value")


def test_summary_lines_format():
    d = EnvDiff(added={"X": "1"}, removed={"Y": "2"}, changed={"Z": ("a", "b")})
    lines = d.summary_lines()
    assert any(l.startswith("+") for l in lines)
    assert any(l.startswith("-") for l in lines)
    assert any(l.startswith("~") for l in lines)


def test_diff_env_file_vs_bytes_missing_file(tmp_path: Path):
    vault_bytes = b"KEY=remote"
    d = diff_env_file_vs_bytes(tmp_path / "nonexistent", vault_bytes)
    assert "KEY" in d.removed  # local is empty, vault has KEY


def test_diff_env_file_vs_bytes_with_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=local_val")
    vault_bytes = b"KEY=remote_val"
    d = diff_env_file_vs_bytes(env_file, vault_bytes)
    assert "KEY" in d.changed
