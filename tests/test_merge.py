"""Tests for envoy.merge."""

import pytest

from envoy.merge import (
    ConflictStrategy,
    MergeConflict,
    MergeResult,
    merge_envs,
)


BASE = "DB_HOST=localhost\nDB_PORT=5432\nAPP_ENV=production\n"
OTHER = "DB_HOST=remotehost\nDB_NAME=mydb\nAPP_ENV=production\n"


def test_merge_adds_new_keys_from_other():
    result = merge_envs(BASE, OTHER)
    assert "DB_NAME" in result.merged
    assert result.merged["DB_NAME"] == "mydb"
    assert "DB_NAME" in result.added


def test_merge_ours_keeps_base_on_conflict():
    result = merge_envs(BASE, OTHER, strategy=ConflictStrategy.OURS)
    assert result.merged["DB_HOST"] == "localhost"
    assert result.success  # OURS silently ignores conflicts
    assert result.overwritten == []


def test_merge_theirs_overwrites_on_conflict():
    result = merge_envs(BASE, OTHER, strategy=ConflictStrategy.THEIRS)
    assert result.merged["DB_HOST"] == "remotehost"
    assert "DB_HOST" in result.overwritten
    assert result.success


def test_merge_error_strategy_records_conflicts():
    result = merge_envs(BASE, OTHER, strategy=ConflictStrategy.ERROR)
    assert not result.success
    keys = [c.key for c in result.conflicts]
    assert "DB_HOST" in keys


def test_merge_no_conflict_when_values_identical():
    identical = "APP_ENV=production\n"
    result = merge_envs(BASE, identical, strategy=ConflictStrategy.ERROR)
    assert result.success
    assert result.conflicts == []


def test_merge_empty_other():
    result = merge_envs(BASE, "")
    assert result.merged == {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "production"}
    assert result.added == []


def test_merge_empty_base():
    result = merge_envs("", OTHER)
    assert set(result.merged.keys()) == {"DB_HOST", "DB_NAME", "APP_ENV"}
    assert set(result.added) == {"DB_HOST", "DB_NAME", "APP_ENV"}


def test_to_env_string_sorted():
    result = merge_envs(BASE, OTHER, strategy=ConflictStrategy.THEIRS)
    env_str = result.to_env_string()
    lines = [l for l in env_str.splitlines() if l]
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys)


def test_summary_contains_counts():
    result = merge_envs(BASE, OTHER, strategy=ConflictStrategy.THEIRS)
    summary = result.summary()
    assert "added" in summary
    assert "overwritten" in summary


def test_merge_conflict_repr():
    c = MergeConflict("KEY", "a", "b")
    assert "KEY" in repr(c)
    assert "a" in repr(c)
    assert "b" in repr(c)


def test_merge_ignores_comments_and_blanks():
    base = "# comment\nKEY=val\n\n"
    other = "KEY=other\n"
    result = merge_envs(base, other, strategy=ConflictStrategy.OURS)
    assert result.merged["KEY"] == "val"
