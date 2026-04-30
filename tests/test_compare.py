"""Tests for envoy.compare module."""
import pytest
from envoy.compare import compare_envs, CompareResult


ENV_A = """
# staging
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=abc123
DEBUG=true
"""

ENV_B = """
# production
DB_HOST=prod.db.example.com
DB_PORT=5432
SECRET_KEY=xyz789
LOG_LEVEL=info
"""


def test_identical_envs_is_clean():
    result = compare_envs(ENV_A, ENV_A, "a", "a")
    assert result.is_identical


def test_only_in_a_detected():
    result = compare_envs(ENV_A, ENV_B)
    assert "DEBUG" in result.only_in_a


def test_only_in_b_detected():
    result = compare_envs(ENV_A, ENV_B)
    assert "LOG_LEVEL" in result.only_in_b


def test_differing_values_detected():
    result = compare_envs(ENV_A, ENV_B)
    keys = [k for k, _, _ in result.differing_values]
    assert "DB_HOST" in keys
    assert "SECRET_KEY" in keys


def test_common_key_same_value_not_in_differing():
    result = compare_envs(ENV_A, ENV_B)
    keys = [k for k, _, _ in result.differing_values]
    assert "DB_PORT" not in keys


def test_mask_values_hides_content():
    result = compare_envs(ENV_A, ENV_B, mask_values=True)
    for _, va, vb in result.differing_values:
        assert va == "***"
        assert vb == "***"


def test_no_mask_shows_values():
    result = compare_envs(ENV_A, ENV_B, mask_values=False)
    db_entry = next((r for r in result.differing_values if r[0] == "DB_HOST"), None)
    assert db_entry is not None
    assert db_entry[1] == "localhost"
    assert db_entry[2] == "prod.db.example.com"


def test_summary_identical():
    result = compare_envs(ENV_A, ENV_A)
    assert "identical" in result.summary().lower()


def test_summary_shows_labels():
    result = compare_envs(ENV_A, ENV_B, label_a="staging", label_b="prod")
    summary = result.summary()
    assert "staging" in summary
    assert "prod" in summary


def test_empty_env_all_in_b():
    result = compare_envs("", ENV_A, "empty", "full")
    assert len(result.only_in_b) > 0
    assert len(result.only_in_a) == 0
    assert result.is_identical is False
