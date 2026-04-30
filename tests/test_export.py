"""Tests for envoy.export."""
import json
import pytest

from envoy.export import export_env, ExportResult

SAMPLE_ENV = """
# comment
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY='my secret'
API_URL="https://example.com"
"""


def test_export_shell_basic():
    result = export_env(SAMPLE_ENV, fmt="shell")
    assert isinstance(result, ExportResult)
    assert result.format == "shell"
    assert result.key_count == 4
    assert "export DB_HOST=localhost" in result.content
    assert "export DB_PORT=5432" in result.content


def test_export_shell_quotes_values_with_spaces():
    result = export_env("MSG='hello world'", fmt="shell")
    assert "export MSG=" in result.content
    assert "hello world" in result.content


def test_export_json_structure():
    result = export_env(SAMPLE_ENV, fmt="json")
    assert result.format == "json"
    data = json.loads(result.content)
    assert data["DB_HOST"] == "localhost"
    assert data["DB_PORT"] == "5432"
    assert data["SECRET_KEY"] == "my secret"
    assert data["API_URL"] == "https://example.com"


def test_export_docker_format():
    result = export_env("PORT=8080\nDEBUG=true", fmt="docker")
    assert result.format == "docker"
    assert "--env PORT=8080" in result.content
    assert "--env DEBUG=true" in result.content


def test_export_ignores_comments_and_blanks():
    text = "# ignore me\n\nKEY=val"
    result = export_env(text, fmt="json")
    data = json.loads(result.content)
    assert list(data.keys()) == ["KEY"]
    assert result.key_count == 1


def test_export_unknown_format_raises():
    with pytest.raises(ValueError, match="Unknown export format"):
        export_env("KEY=val", fmt="yaml")  # type: ignore[arg-type]


def test_export_result_repr():
    result = export_env("A=1", fmt="shell")
    assert "ExportResult" in repr(result)


def test_export_empty_env():
    result = export_env("", fmt="json")
    assert result.key_count == 0
    assert json.loads(result.content) == {}
