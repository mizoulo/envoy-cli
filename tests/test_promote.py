"""Tests for envoy.promote."""
from pathlib import Path

import pytest

from envoy.vault import Vault
from envoy.promote import PromoteResult, promote_env


PASSWORD = "test-secret"


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    return Vault(storage_dir=str(tmp_path))


def _push(vault: Vault, project: str, env: str, content: str) -> None:
    vault.push(project, env, content, PASSWORD)


def _pull(vault: Vault, project: str, env: str) -> str:
    return vault.pull(project, env, PASSWORD)


# ---------------------------------------------------------------------------
# PromoteResult
# ---------------------------------------------------------------------------

def test_promote_result_success_when_no_error():
    r = PromoteResult(source="staging", target="production", keys_copied=3)
    assert r.success is True


def test_promote_result_failure_when_error():
    r = PromoteResult(source="staging", target="production", keys_copied=0, error="boom")
    assert r.success is False


def test_promote_result_repr_contains_fields():
    r = PromoteResult(source="staging", target="production", keys_copied=2, skipped_keys=["SECRET"])
    text = repr(r)
    assert "staging" in text
    assert "production" in text


# ---------------------------------------------------------------------------
# promote_env — happy path
# ---------------------------------------------------------------------------

def test_promote_copies_all_keys(vault):
    _push(vault, "myapp", "staging", "FOO=bar\nBAZ=qux")
    result = promote_env(vault, "myapp", "staging", "production", PASSWORD)
    assert result.success
    assert result.keys_copied == 2
    pulled = _pull(vault, "myapp", "production")
    assert "FOO=bar" in pulled
    assert "BAZ=qux" in pulled


def test_promote_skips_specified_keys(vault):
    _push(vault, "myapp", "staging", "FOO=bar\nSECRET=hunter2")
    result = promote_env(vault, "myapp", "staging", "production", PASSWORD, skip_keys=["SECRET"])
    assert result.success
    assert result.keys_copied == 1
    assert "SECRET" in result.skipped_keys
    pulled = _pull(vault, "myapp", "production")
    assert "FOO=bar" in pulled
    assert "SECRET" not in pulled


def test_promote_no_overwrite_preserves_target(vault):
    _push(vault, "myapp", "staging", "FOO=from_staging")
    _push(vault, "myapp", "production", "FOO=from_prod")
    result = promote_env(vault, "myapp", "staging", "production", PASSWORD, overwrite=False)
    assert result.success
    assert result.keys_copied == 0
    assert "FOO" in result.skipped_keys
    pulled = _pull(vault, "myapp", "production")
    assert "FOO=from_prod" in pulled


def test_promote_overwrite_replaces_target(vault):
    _push(vault, "myapp", "staging", "FOO=from_staging")
    _push(vault, "myapp", "production", "FOO=from_prod")
    result = promote_env(vault, "myapp", "staging", "production", PASSWORD, overwrite=True)
    assert result.success
    assert result.keys_copied == 1
    pulled = _pull(vault, "myapp", "production")
    assert "FOO=from_staging" in pulled


def test_promote_source_missing_returns_error(vault):
    result = promote_env(vault, "myapp", "nonexistent", "production", PASSWORD)
    assert not result.success
    assert result.error is not None
    assert result.keys_copied == 0


def test_promote_ignores_comments_and_blank_lines(vault):
    content = "# comment\n\nFOO=bar\n   \nBAZ=1"
    _push(vault, "myapp", "staging", content)
    result = promote_env(vault, "myapp", "staging", "production", PASSWORD)
    assert result.success
    assert result.keys_copied == 2
