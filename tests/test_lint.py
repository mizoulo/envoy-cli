"""Tests for envoy.lint module."""
import pytest
from pathlib import Path
from envoy.lint import lint_env, lint_file, LintIssue, LintResult


def test_clean_env_returns_no_issues():
    src = "DB_HOST=localhost\nDB_PORT=5432\n"
    result = lint_env(src)
    assert result.clean
    assert result.issues == []


def test_comments_and_blanks_are_ignored():
    src = "# comment\n\nAPP_ENV=production\n"
    result = lint_env(src)
    assert result.clean


def test_invalid_line_format_raises_e001():
    src = "THIS IS NOT VALID\n"
    result = lint_env(src)
    codes = [i.code for i in result.issues]
    assert "E001" in codes


def test_lowercase_key_raises_w001():
    src = "db_host=localhost\n"
    result = lint_env(src)
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_duplicate_key_raises_e002():
    src = "APP_ENV=dev\nAPP_ENV=prod\n"
    result = lint_env(src)
    codes = [i.code for i in result.issues]
    assert "E002" in codes


def test_value_leading_whitespace_raises_w002():
    src = "APP_KEY= secret\n"
    result = lint_env(src)
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_multiple_issues_collected():
    src = "db_host=localhost\ndb_host= value\n"
    result = lint_env(src)
    assert len(result.issues) >= 3  # W001 x2 + E002


def test_result_not_clean_when_issues_present():
    src = "bad line\n"
    result = lint_env(src)
    assert not result.clean


def test_summary_ok_when_clean():
    result = lint_env("APP=1\n", path=".env")
    assert result.summary() == ".env: OK"


def test_summary_contains_issue_count():
    result = lint_env("bad line\n", path=".env")
    assert "1 issue" in result.summary()


def test_lint_file_reads_from_disk(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=envoy\nAPP_ENV=test\n")
    result = lint_file(env_file)
    assert result.clean


def test_lint_issue_repr():
    issue = LintIssue(line_no=3, code="E001", message="bad")
    assert "L3" in repr(issue)
    assert "E001" in repr(issue)
