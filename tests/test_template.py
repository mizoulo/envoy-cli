"""Tests for envoy.template."""
from pathlib import Path

import pytest

from envoy.template import (
    RenderResult,
    collect_placeholders,
    render_template,
    render_template_file,
)


def test_render_basic_substitution():
    result = render_template("DB_HOST={{ HOST }}\nDB_PORT={{ PORT }}", {"HOST": "localhost", "PORT": "5432"})
    assert result.output == "DB_HOST=localhost\nDB_PORT=5432"
    assert result.success
    assert set(result.substituted) == {"HOST", "PORT"}
    assert result.missing == []


def test_render_missing_variable_kept_in_output():
    result = render_template("API_KEY={{ API_KEY }}", {})
    assert "{{ API_KEY }}" in result.output
    assert "API_KEY" in result.missing
    assert not result.success


def test_render_partial_substitution():
    result = render_template("A={{ A }}\nB={{ B }}", {"A": "1"})
    assert "A=1" in result.output
    assert "{{ B }}" in result.output
    assert result.substituted == ["A"]
    assert result.missing == ["B"]


def test_render_duplicate_placeholder_counted_once():
    result = render_template("{{ X }} and {{ X }}", {"X": "hello"})
    assert result.output == "hello and hello"
    assert result.substituted == ["X"]


def test_render_missing_deduped():
    result = render_template("{{ Z }} {{ Z }}", {})
    assert result.missing == ["Z"]


def test_render_result_repr():
    r = RenderResult(output="x", substituted=["A"], missing=["B"])
    assert "RenderResult" in repr(r)


def test_collect_placeholders_basic():
    placeholders = collect_placeholders("{{ FOO }} and {{ BAR }} and {{ FOO }}")
    assert placeholders == ["FOO", "BAR"]


def test_collect_placeholders_empty():
    assert collect_placeholders("no placeholders here") == []


def test_render_template_file_reads_and_writes(tmp_path: Path):
    tmpl = tmp_path / "template.env"
    tmpl.write_text("SECRET={{ SECRET }}\n", encoding="utf-8")
    out = tmp_path / ".env"
    result = render_template_file(tmpl, {"SECRET": "abc123"}, output_path=out)
    assert result.success
    assert out.read_text() == "SECRET=abc123\n"


def test_render_template_file_no_output_path(tmp_path: Path):
    tmpl = tmp_path / "template.env"
    tmpl.write_text("KEY={{ KEY }}", encoding="utf-8")
    result = render_template_file(tmpl, {"KEY": "val"})
    assert result.output == "KEY=val"
    assert not (tmp_path / ".env").exists()
