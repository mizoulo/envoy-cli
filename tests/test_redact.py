"""Tests for envoy.redact."""
import pytest
from envoy.redact import redact_env, _is_sensitive, _mask_value, RedactResult


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_api_key():
    assert _is_sensitive("STRIPE_API_KEY") is True


def test_is_sensitive_token():
    assert _is_sensitive("ACCESS_TOKEN") is True


def test_is_sensitive_normal_key():
    assert _is_sensitive("APP_ENV") is False


# ---------------------------------------------------------------------------
# _mask_value
# ---------------------------------------------------------------------------

def test_mask_value_full():
    assert _mask_value("supersecret") == "***"


def test_mask_value_partial_long():
    result = _mask_value("supersecret", partial=True)
    assert result.endswith("cret")
    assert result.startswith("***")


def test_mask_value_partial_short():
    # Value shorter than _PARTIAL_VISIBLE → fully masked
    assert _mask_value("abc", partial=True) == "***"


def test_mask_value_empty():
    assert _mask_value("") == ""


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------

ENV_CONTENT = """
# database config
DB_HOST=localhost
DB_PASSWORD=hunter2
DB_USER=admin
API_KEY=sk-abc123
APP_ENV=production
""".strip()


def test_redact_counts():
    result = redact_env(ENV_CONTENT)
    assert result.original_count == 5
    assert result.redacted_count == 2


def test_redact_masks_password():
    result = redact_env(ENV_CONTENT)
    joined = "\n".join(result.lines)
    assert "hunter2" not in joined
    assert "DB_PASSWORD=***" in joined


def test_redact_masks_api_key():
    result = redact_env(ENV_CONTENT)
    joined = "\n".join(result.lines)
    assert "sk-abc123" not in joined


def test_redact_preserves_non_sensitive():
    result = redact_env(ENV_CONTENT)
    joined = "\n".join(result.lines)
    assert "DB_HOST=localhost" in joined
    assert "APP_ENV=production" in joined


def test_redact_preserves_comments():
    result = redact_env(ENV_CONTENT)
    assert any(line.startswith("#") for line in result.lines)


def test_redact_extra_keys():
    result = redact_env(ENV_CONTENT, extra_keys=["DB_USER"])
    joined = "\n".join(result.lines)
    assert "admin" not in joined
    assert result.redacted_count == 3


def test_redact_partial_reveals_suffix():
    result = redact_env(ENV_CONTENT, partial=True)
    joined = "\n".join(result.lines)
    # sk-abc123 → last 4 chars are '123' + one more; value is 'sk-abc123'
    assert "123" in joined  # partial reveal
    assert "sk-abc" not in joined


def test_redact_summary():
    result = redact_env(ENV_CONTENT)
    assert "2/5" in result.summary


def test_empty_content():
    result = redact_env("")
    assert result.original_count == 0
    assert result.redacted_count == 0
