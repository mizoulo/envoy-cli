"""Tests for envoy.mask."""

import pytest
from envoy.mask import (
    MaskReport,
    MaskResult,
    _is_sensitive,
    _mask_value,
    mask_env,
    DEFAULT_MASK,
)


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


def test_is_sensitive_case_insensitive():
    assert _is_sensitive("db_secret") is True


# ---------------------------------------------------------------------------
# _mask_value
# ---------------------------------------------------------------------------

def test_mask_value_reveals_prefix():
    result = _mask_value("supersecret", reveal_chars=4)
    assert result == "supe" + DEFAULT_MASK


def test_mask_value_short_value_fully_masked():
    result = _mask_value("abc", reveal_chars=4)
    assert result == DEFAULT_MASK


def test_mask_value_empty_string():
    assert _mask_value("") == DEFAULT_MASK


def test_mask_value_custom_mask():
    result = _mask_value("hello_world", reveal_chars=2, mask="[hidden]")
    assert result == "he[hidden]"


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------

def test_mask_env_sensitive_keys_are_masked():
    env = {"DB_PASSWORD": "s3cr3t", "APP_ENV": "production"}
    report = mask_env(env)
    assert report.sensitive_count == 1
    assert report.plain_count == 1
    masked = report.as_dict()
    assert masked["APP_ENV"] == "production"
    assert masked["DB_PASSWORD"] != "s3cr3t"


def test_mask_env_force_mask_overrides_plain_key():
    env = {"APP_URL": "https://example.com"}
    report = mask_env(env, force_mask=["APP_URL"])
    assert report.sensitive_count == 1
    assert report.as_dict()["APP_URL"].endswith(DEFAULT_MASK)


def test_mask_env_force_reveal_overrides_sensitive_key():
    env = {"API_TOKEN": "tok_abc123"}
    report = mask_env(env, force_reveal=["API_TOKEN"])
    assert report.sensitive_count == 0
    assert report.as_dict()["API_TOKEN"] == "tok_abc123"


def test_mask_env_summary_string():
    env = {"SECRET_KEY": "abc", "PORT": "8080"}
    report = mask_env(env)
    summary = report.summary()
    assert "2 keys" in summary
    assert "1 masked" in summary
    assert "1 visible" in summary


def test_mask_env_empty_env():
    report = mask_env({})
    assert report.results == []
    assert report.summary() == "0 keys (0 masked, 0 visible)"
