"""Tests for envoy.quota."""
import json
import pytest
from pathlib import Path
from envoy.quota import QuotaManager, QuotaPolicy, QuotaResult


@pytest.fixture
def manager(tmp_path):
    return QuotaManager(tmp_path / "quotas.json")


def test_quota_result_allowed():
    r = QuotaResult(action="add", key="FOO", allowed=True)
    assert r.success() is True
    assert "allowed" in repr(r)


def test_quota_result_denied():
    r = QuotaResult(action="add", key="FOO", allowed=False, reason="too many keys")
    assert r.success() is False
    assert "denied" in repr(r)
    assert "too many keys" in repr(r)


def test_policy_file_created_on_set(manager, tmp_path):
    policy = QuotaPolicy(max_keys=10)
    manager.set_policy("myproject", policy)
    assert (tmp_path / "quotas.json").exists()


def test_get_default_policy_when_not_set(manager):
    policy = manager.get_policy("unknown")
    assert policy.max_keys == 100
    assert policy.max_value_bytes == 4096


def test_set_and_get_policy(manager):
    policy = QuotaPolicy(max_keys=5, max_value_bytes=512, max_key_length=32)
    manager.set_policy("proj", policy)
    loaded = manager.get_policy("proj")
    assert loaded.max_keys == 5
    assert loaded.max_value_bytes == 512
    assert loaded.max_key_length == 32


def test_policy_persists_across_instances(tmp_path):
    p = tmp_path / "quotas.json"
    m1 = QuotaManager(p)
    m1.set_policy("proj", QuotaPolicy(max_keys=7))
    m2 = QuotaManager(p)
    assert m2.get_policy("proj").max_keys == 7


def test_check_add_key_allowed(manager):
    result = manager.check_add_key("proj", "MY_KEY", "somevalue", current_keys=5)
    assert result.allowed is True


def test_check_add_key_too_many_keys(manager):
    manager.set_policy("proj", QuotaPolicy(max_keys=3))
    result = manager.check_add_key("proj", "NEW_KEY", "val", current_keys=3)
    assert result.allowed is False
    assert "max" in result.reason


def test_check_add_key_value_too_large(manager):
    manager.set_policy("proj", QuotaPolicy(max_value_bytes=10))
    result = manager.check_add_key("proj", "KEY", "x" * 20, current_keys=0)
    assert result.allowed is False
    assert "value size" in result.reason


def test_check_add_key_key_too_long(manager):
    manager.set_policy("proj", QuotaPolicy(max_key_length=5))
    result = manager.check_add_key("proj", "TOOLONGKEY", "val", current_keys=0)
    assert result.allowed is False
    assert "key length" in result.reason


def test_remove_policy(manager):
    manager.set_policy("proj", QuotaPolicy(max_keys=2))
    removed = manager.remove_policy("proj")
    assert removed is True
    assert manager.get_policy("proj").max_keys == 100  # back to default


def test_remove_nonexistent_policy(manager):
    assert manager.remove_policy("ghost") is False
