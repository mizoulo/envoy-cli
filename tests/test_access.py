"""Tests for envoy.access module."""
import json
import pytest
from pathlib import Path
from envoy.access import AccessManager, AccessRule, AccessResult


@pytest.fixture
def rules_path(tmp_path: Path) -> Path:
    return tmp_path / "access_rules.json"


@pytest.fixture
def manager(rules_path: Path) -> AccessManager:
    return AccessManager(rules_path)


def test_access_result_bool_true():
    r = AccessResult(allowed=True, key="DB_PASS", permission="read")
    assert bool(r) is True


def test_access_result_bool_false():
    r = AccessResult(allowed=False, key="DB_PASS", permission="write")
    assert bool(r) is False


def test_access_result_repr_contains_key():
    r = AccessResult(allowed=True, key="API_KEY", permission="read")
    assert "API_KEY" in repr(r)
    assert "allowed" in repr(r)


def test_no_rules_allows_everything(manager: AccessManager):
    result = manager.check("ANY_KEY", "write")
    assert result.allowed is True
    assert result.rule is None


def test_add_rule_persists(manager: AccessManager, rules_path: Path):
    manager.add_rule("SECRET_*", "none")
    data = json.loads(rules_path.read_text())
    assert len(data["rules"]) == 1
    assert data["rules"][0]["pattern"] == "SECRET_*"


def test_rule_blocks_write(manager: AccessManager):
    manager.add_rule("DB_*", "none")
    result = manager.check("DB_PASSWORD", "write")
    assert result.allowed is False


def test_rule_allows_read_with_read_permission(manager: AccessManager):
    manager.add_rule("DB_*", "read")
    result = manager.check("DB_HOST", "read")
    assert result.allowed is True


def test_rule_blocks_write_with_read_only_permission(manager: AccessManager):
    manager.add_rule("DB_*", "read")
    result = manager.check("DB_HOST", "write")
    assert result.allowed is False


def test_last_matching_rule_wins(manager: AccessManager):
    manager.add_rule("*", "none")
    manager.add_rule("PUBLIC_*", "write")
    result = manager.check("PUBLIC_URL", "write")
    assert result.allowed is True


def test_remove_rule(manager: AccessManager):
    manager.add_rule("SECRET_*", "none")
    removed = manager.remove_rule("SECRET_*")
    assert removed is True
    assert manager.list_rules() == []


def test_remove_nonexistent_rule_returns_false(manager: AccessManager):
    removed = manager.remove_rule("DOES_NOT_EXIST")
    assert removed is False


def test_list_rules_returns_all(manager: AccessManager):
    manager.add_rule("A_*", "read")
    manager.add_rule("B_*", "write")
    rules = manager.list_rules()
    assert len(rules) == 2
    assert rules[0].pattern == "A_*"


def test_load_from_existing_file(rules_path: Path, tmp_path: Path):
    rules_path.write_text(json.dumps({"rules": [{"pattern": "X_*", "permission": "none", "note": ""}]}))
    m = AccessManager(rules_path)
    assert len(m.list_rules()) == 1
    assert m.list_rules()[0].pattern == "X_*"
