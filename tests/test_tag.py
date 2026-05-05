"""Tests for envoy.tag module."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envoy.tag import TagManager, TagResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(tmp_path: Path):
    """Return a lightweight mock vault backed by an in-memory dict."""
    store: dict = {}

    def push(project, key, value):
        store[(project, key)] = value

    def pull(project, key):
        if (project, key) not in store:
            raise KeyError(key)
        return store[(project, key)]

    def list_envs(project):
        prefix = f"__tags__/{project}/"
        return [
            k[1].replace(prefix, "")
            for k in store
            if k[1].startswith(prefix)
        ]

    vault = MagicMock()
    vault.push.side_effect = push
    vault.pull.side_effect = pull
    vault.list_envs.side_effect = list_envs
    return vault


@pytest.fixture
def manager(tmp_path):
    return TagManager(_make_vault(tmp_path))


# ---------------------------------------------------------------------------
# TagResult
# ---------------------------------------------------------------------------

def test_tag_result_success_when_no_errors():
    r = TagResult(added=["prod"])
    assert r.success is True


def test_tag_result_failure_when_errors():
    r = TagResult(errors=["boom"])
    assert r.success is False


def test_tag_result_repr_contains_counts():
    r = TagResult(added=["a", "b"], removed=["c"], errors=[])
    assert "added=2" in repr(r)
    assert "removed=1" in repr(r)


# ---------------------------------------------------------------------------
# TagManager
# ---------------------------------------------------------------------------

def test_add_new_tags(manager):
    result = manager.add("myapp", "production", ["live", "critical"])
    assert result.success
    assert set(result.added) == {"live", "critical"}


def test_add_duplicate_tag_not_added_twice(manager):
    manager.add("myapp", "production", ["live"])
    result = manager.add("myapp", "production", ["live", "new"])
    assert "new" in result.added
    assert "live" not in result.added
    assert manager.list_tags("myapp", "production").count("live") == 1


def test_remove_existing_tag(manager):
    manager.add("myapp", "staging", ["draft", "wip"])
    result = manager.remove("myapp", "staging", ["wip"])
    assert result.success
    assert "wip" in result.removed
    assert "wip" not in manager.list_tags("myapp", "staging")


def test_remove_nonexistent_tag_is_noop(manager):
    result = manager.remove("myapp", "staging", ["ghost"])
    assert result.success
    assert result.removed == []


def test_list_tags_empty_for_unknown_env(manager):
    assert manager.list_tags("myapp", "unknown") == []


def test_find_by_tag_returns_matching_envs(manager):
    manager.add("myapp", "prod", ["live"])
    manager.add("myapp", "staging", ["live", "test"])
    manager.add("myapp", "dev", ["test"])
    matches = manager.find_by_tag("myapp", "live")
    assert set(matches) == {"prod", "staging"}
