"""Tests for envoy.deps — dependency tracking for .env files."""
import pytest
from pathlib import Path

from envoy.deps import DepGraph, DepResult, _parse_env, _extract_refs


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def test_parse_env_basic():
    text = "FOO=bar\nBAZ=qux\n"
    assert _parse_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments_and_blanks():
    text = "# comment\n\nFOO=1\n"
    assert _parse_env(text) == {"FOO": "1"}


def test_extract_refs_dollar_brace():
    assert _extract_refs("${FOO}/bin") == {"FOO"}


def test_extract_refs_plain_dollar():
    assert _extract_refs("$BAR_2") == {"BAR_2"}


def test_extract_refs_mixed():
    refs = _extract_refs("${HOST}:$PORT")
    assert refs == {"HOST", "PORT"}


def test_extract_refs_no_refs():
    assert _extract_refs("plain-value") == set()


# ---------------------------------------------------------------------------
# DepGraph
# ---------------------------------------------------------------------------

@pytest.fixture()
def graph(tmp_path: Path) -> DepGraph:
    return DepGraph(_index_path=tmp_path / "deps.json")


def test_record_creates_index_file(graph: DepGraph, tmp_path: Path):
    graph.record("app/.env", "URL=${BASE_URL}/api\n")
    assert (tmp_path / "deps.json").exists()


def test_record_captures_external_refs(graph: DepGraph):
    graph.record("app/.env", "URL=${BASE_URL}/api\nBASE_URL=http://localhost\n")
    # BASE_URL is defined locally, so not external
    deps = graph.all_deps()
    assert deps["app/.env"] == []


def test_record_captures_truly_external(graph: DepGraph):
    graph.record("app/.env", "URL=${BASE_URL}/api\n")
    deps = graph.all_deps()
    assert "BASE_URL" in deps["app/.env"]


def test_check_all_satisfied(graph: DepGraph):
    graph.record("app/.env", "URL=${BASE_URL}/api\n")
    result = graph.check("app/.env", "BASE_URL=http://example.com\n")
    assert result.success
    assert "BASE_URL" in result.satisfied
    assert result.missing == []


def test_check_missing_keys(graph: DepGraph):
    graph.record("app/.env", "URL=${BASE_URL}/api\nDB=${DB_HOST}\n")
    result = graph.check("app/.env", "BASE_URL=http://example.com\n")
    assert not result.success
    assert "DB_HOST" in result.missing
    assert "BASE_URL" in result.satisfied


def test_check_unknown_source_returns_empty(graph: DepGraph):
    result = graph.check("nonexistent/.env", "FOO=bar\n")
    assert result.success
    assert result.missing == []
    assert result.satisfied == []


def test_dep_result_repr_contains_source():
    r = DepResult(source="app/.env", missing=["X"], satisfied=["Y"])
    assert "app/.env" in repr(r)
    assert "missing" in repr(r)


def test_all_deps_returns_full_graph(graph: DepGraph):
    graph.record("a/.env", "X=${EXT}\n")
    graph.record("b/.env", "Y=static\n")
    deps = graph.all_deps()
    assert "a/.env" in deps
    assert "b/.env" in deps
