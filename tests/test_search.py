"""Tests for envoy.search."""
import pytest

from envoy.vault import Vault
from envoy.search import EnvSearcher, SearchMatch, SearchResult

PASSWORD = "test-password"


@pytest.fixture()
def vault(tmp_path):
    return Vault(storage_dir=str(tmp_path))


@pytest.fixture()
def populated_vault(vault):
    vault.push("myapp", "production", "DB_HOST=prod.db\nDB_PORT=5432\nSECRET_KEY=abc123\n", PASSWORD)
    vault.push("myapp", "staging", "DB_HOST=staging.db\nDB_PORT=5432\nDEBUG=true\n", PASSWORD)
    vault.push("otherapp", "production", "API_KEY=xyz\nDB_HOST=other.db\n", PASSWORD)
    return vault


def test_search_result_found(populated_vault):
    searcher = EnvSearcher(populated_vault, PASSWORD)
    result = searcher.search("DB_HOST", "myapp")
    assert result.found
    assert len(result.matches) == 2


def test_search_result_not_found(populated_vault):
    searcher = EnvSearcher(populated_vault, PASSWORD)
    result = searcher.search("NONEXISTENT_KEY", "myapp")
    assert not result.found
    assert result.summary().startswith("No matches")


def test_search_keys_only(populated_vault):
    searcher = EnvSearcher(populated_vault, PASSWORD)
    result = searcher.search("DB", "myapp", keys_only=True)
    # DB_HOST and DB_PORT in both envs => 4 matches
    assert len(result.matches) == 4
    for match in result.matches:
        assert "=" not in match.line.split("=", 1)[0]


def test_search_ignore_case(populated_vault):
    searcher = EnvSearcher(populated_vault, PASSWORD)
    result = searcher.search("debug", "myapp", ignore_case=True)
    assert result.found
    assert result.matches[0].line == "DEBUG=true"


def test_search_match_repr(populated_vault):
    searcher = EnvSearcher(populated_vault, PASSWORD)
    result = searcher.search("SECRET_KEY", "myapp")
    assert result.found
    r = repr(result.matches[0])
    assert "myapp" in r
    assert "SECRET_KEY" in r


def test_search_result_summary_with_matches(populated_vault):
    searcher = EnvSearcher(populated_vault, PASSWORD)
    result = searcher.search("DB_PORT", "myapp")
    assert "2 match" in result.summary()


def test_search_skips_comments_and_blanks(vault):
    vault.push("proj", "dev", "# DB_HOST=comment\n\nDB_HOST=real.db\n", PASSWORD)
    searcher = EnvSearcher(vault, PASSWORD)
    result = searcher.search("DB_HOST", "proj")
    assert len(result.matches) == 1
    assert result.matches[0].line == "DB_HOST=real.db"
