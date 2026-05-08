"""Tests for envoy.resolve."""
import pytest
from envoy.resolve import resolve_env, ResolveResult


DEFINED = """
BASE=/app
DATA=${BASE}/data
LOG=${DATA}/logs
"""

MISSING_REF = """
HOME=/home/user
CONFIG=${HOME}/config
DEBUG=${UNDEFINED_VAR}/debug
"""

CYCLE = """
A=${B}
B=${A}
"""

SIMPLE = """
FOO=hello
BAR=world
"""


def test_resolve_basic_substitution():
    result = resolve_env(DEFINED)
    assert result.success
    assert result.resolved["BASE"] == "/app"
    assert result.resolved["DATA"] == "/app/data"
    assert result.resolved["LOG"] == "/app/data/logs"


def test_resolve_no_references():
    result = resolve_env(SIMPLE)
    assert result.success
    assert result.resolved["FOO"] == "hello"
    assert result.resolved["BAR"] == "world"
    assert result.unresolved == []
    assert result.cycles == []


def test_resolve_missing_reference_recorded():
    result = resolve_env(MISSING_REF)
    assert "DEBUG" in result.unresolved
    assert "HOME" not in result.unresolved
    assert "CONFIG" not in result.unresolved


def test_resolve_missing_reference_still_expands_known():
    result = resolve_env(MISSING_REF)
    assert result.resolved["CONFIG"] == "/home/user/config"


def test_resolve_cycle_detected():
    result = resolve_env(CYCLE)
    assert len(result.cycles) > 0
    assert not result.success


def test_resolve_empty_string():
    result = resolve_env("")
    assert result.success
    assert result.resolved == {}


def test_resolve_ignores_comments_and_blanks():
    text = "# comment\n\nKEY=value\n"
    result = resolve_env(text)
    assert "KEY" in result.resolved
    assert result.resolved["KEY"] == "value"


def test_resolve_result_repr_contains_counts():
    result = ResolveResult(resolved={"A": "1"}, unresolved=["B"], cycles=[])
    r = repr(result)
    assert "resolved=1" in r
    assert "unresolved=['B']" in r


def test_resolve_result_success_false_when_cycle():
    result = ResolveResult(cycles=["A"])
    assert not result.success


def test_resolve_result_success_false_when_error():
    result = ResolveResult(error="something went wrong")
    assert not result.success


def test_resolve_missing_reference_success_is_false():
    """A missing variable reference should mark the result as not fully successful."""
    result = resolve_env(MISSING_REF)
    assert not result.success
