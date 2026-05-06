"""Tests for envoy.validate."""
import pytest
from envoy.validate import validate_env, ValidationResult, ValidationIssue


SCHEMA = """
DB_HOST=required
DB_PORT=required
SECRET_KEY=required
OPTIONAL_FEATURE=?optional
"""


def test_valid_env_passes():
    env = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n"
    result = validate_env(env, SCHEMA)
    assert result.valid is True
    assert result.issues == []


def test_missing_required_key_is_error():
    env = "DB_HOST=localhost\nDB_PORT=5432\n"  # missing SECRET_KEY
    result = validate_env(env, SCHEMA)
    assert result.valid is False
    keys = [i.key for i in result.issues]
    assert "SECRET_KEY" in keys
    issue = next(i for i in result.issues if i.key == "SECRET_KEY")
    assert issue.severity == "error"


def test_missing_optional_key_is_warning():
    env = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc\n"
    result = validate_env(env, SCHEMA)
    assert result.valid is True  # warnings don't fail
    keys = [i.key for i in result.issues]
    assert "OPTIONAL_FEATURE" in keys
    issue = next(i for i in result.issues if i.key == "OPTIONAL_FEATURE")
    assert issue.severity == "warning"


def test_empty_required_value_is_error():
    env = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=\n"
    result = validate_env(env, SCHEMA)
    assert result.valid is False
    issue = next(i for i in result.issues if i.key == "SECRET_KEY")
    assert issue.severity == "error"
    assert "empty" in issue.message


def test_extra_keys_allowed_by_default():
    env = "DB_HOST=h\nDB_PORT=5\nSECRET_KEY=k\nEXTRA=foo\n"
    result = validate_env(env, SCHEMA)
    assert result.valid is True
    assert all(i.key != "EXTRA" for i in result.issues)


def test_extra_keys_flagged_when_not_allowed():
    env = "DB_HOST=h\nDB_PORT=5\nSECRET_KEY=k\nEXTRA=foo\n"
    result = validate_env(env, SCHEMA, allow_extra=False)
    keys = [i.key for i in result.issues]
    assert "EXTRA" in keys
    issue = next(i for i in result.issues if i.key == "EXTRA")
    assert issue.severity == "warning"


def test_summary_clean():
    env = "DB_HOST=h\nDB_PORT=5\nSECRET_KEY=k\n"
    result = validate_env(env, SCHEMA)
    assert "All required keys" in result.summary()


def test_summary_failed_contains_status():
    env = "DB_HOST=h\n"
    result = validate_env(env, SCHEMA)
    summary = result.summary()
    assert "FAILED" in summary


def test_issue_repr():
    issue = ValidationIssue("MY_KEY", "Some problem.", "error")
    assert "ERROR" in repr(issue)
    assert "MY_KEY" in repr(issue)


def test_multiple_missing_required_keys_all_reported():
    """All missing required keys should appear in issues, not just the first."""
    env = ""  # no keys at all
    result = validate_env(env, SCHEMA)
    assert result.valid is False
    error_keys = [i.key for i in result.issues if i.severity == "error"]
    assert "DB_HOST" in error_keys
    assert "DB_PORT" in error_keys
    assert "SECRET_KEY" in error_keys
