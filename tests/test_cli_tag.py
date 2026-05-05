"""Tests for envoy.cli_tag CLI commands."""
import json
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from envoy.cli_tag import tag_cli


@pytest.fixture
def runner():
    return CliRunner()


def _vault_with_store():
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


@pytest.fixture(autouse=True)
def mock_vault():
    vault = _vault_with_store()
    with patch("envoy.cli_tag._make_vault", return_value=vault):
        yield vault


def test_add_tag_success(runner):
    result = runner.invoke(
        tag_cli, ["add", "myapp", "prod", "live", "--password", "secret"]
    )
    assert result.exit_code == 0
    assert "Added" in result.output
    assert "live" in result.output


def test_add_duplicate_tag_reports_no_new(runner):
    runner.invoke(tag_cli, ["add", "myapp", "prod", "live", "--password", "secret"])
    result = runner.invoke(
        tag_cli, ["add", "myapp", "prod", "live", "--password", "secret"]
    )
    assert result.exit_code == 0
    assert "No new tags" in result.output


def test_remove_tag_success(runner):
    runner.invoke(tag_cli, ["add", "myapp", "prod", "draft", "--password", "s"])
    result = runner.invoke(
        tag_cli, ["remove", "myapp", "prod", "draft", "--password", "s"]
    )
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_nonexistent_tag_is_noop(runner):
    result = runner.invoke(
        tag_cli, ["remove", "myapp", "prod", "ghost", "--password", "s"]
    )
    assert result.exit_code == 0
    assert "Nothing to remove" in result.output


def test_list_tags_shows_tags(runner):
    runner.invoke(tag_cli, ["add", "myapp", "prod", "live", "critical", "--password", "s"])
    result = runner.invoke(tag_cli, ["list", "myapp", "prod", "--password", "s"])
    assert result.exit_code == 0
    assert "live" in result.output
    assert "critical" in result.output


def test_list_tags_empty(runner):
    result = runner.invoke(tag_cli, ["list", "myapp", "unknown", "--password", "s"])
    assert result.exit_code == 0
    assert "No tags found" in result.output


def test_find_by_tag(runner):
    runner.invoke(tag_cli, ["add", "myapp", "prod", "live", "--password", "s"])
    runner.invoke(tag_cli, ["add", "myapp", "staging", "live", "--password", "s"])
    result = runner.invoke(tag_cli, ["find", "myapp", "live", "--password", "s"])
    assert result.exit_code == 0
    assert "prod" in result.output
    assert "staging" in result.output


def test_find_no_matches(runner):
    result = runner.invoke(tag_cli, ["find", "myapp", "nope", "--password", "s"])
    assert result.exit_code == 0
    assert "No envs tagged" in result.output
