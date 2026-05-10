"""Tests for envoy.cli_sign."""
import pytest
from pathlib import Path
from click.testing import CliRunner
from envoy.cli_sign import sign_cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("API_KEY=abc123\nDEBUG=false\n")
    return p


@pytest.fixture
def sign_dir(tmp_path: Path) -> str:
    return str(tmp_path / "signs")


def test_sign_outputs_confirmation(runner, env_file, sign_dir):
    result = runner.invoke(
        sign_cli, ["sign", "proj/dev", str(env_file), "--secret", "mysecret", "--sign-dir", sign_dir]
    )
    assert result.exit_code == 0
    assert "Signed" in result.output
    assert "proj/dev" in result.output


def test_verify_success_after_sign(runner, env_file, sign_dir):
    runner.invoke(
        sign_cli, ["sign", "proj/dev", str(env_file), "--secret", "mysecret", "--sign-dir", sign_dir]
    )
    result = runner.invoke(
        sign_cli, ["verify", "proj/dev", str(env_file), "--secret", "mysecret", "--sign-dir", sign_dir]
    )
    assert result.exit_code == 0
    assert "Verified" in result.output


def test_verify_fails_on_tampered_file(runner, env_file, sign_dir, tmp_path):
    runner.invoke(
        sign_cli, ["sign", "proj/dev", str(env_file), "--secret", "mysecret", "--sign-dir", sign_dir]
    )
    env_file.write_text("API_KEY=HACKED\n")
    result = runner.invoke(
        sign_cli, ["verify", "proj/dev", str(env_file), "--secret", "mysecret", "--sign-dir", sign_dir]
    )
    assert result.exit_code != 0


def test_verify_missing_key_exits_nonzero(runner, env_file, sign_dir):
    result = runner.invoke(
        sign_cli, ["verify", "missing/key", str(env_file), "--secret", "mysecret", "--sign-dir", sign_dir]
    )
    assert result.exit_code != 0


def test_remove_existing_key(runner, env_file, sign_dir):
    runner.invoke(
        sign_cli, ["sign", "proj/dev", str(env_file), "--secret", "mysecret", "--sign-dir", sign_dir]
    )
    result = runner.invoke(sign_cli, ["remove", "proj/dev", "--sign-dir", sign_dir])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_missing_key_exits_nonzero(runner, sign_dir):
    result = runner.invoke(sign_cli, ["remove", "nonexistent", "--sign-dir", sign_dir])
    assert result.exit_code != 0


def test_list_empty_shows_message(runner, sign_dir):
    result = runner.invoke(sign_cli, ["list", "--sign-dir", sign_dir])
    assert result.exit_code == 0
    assert "No signatures" in result.output


def test_list_shows_signed_keys(runner, env_file, sign_dir):
    runner.invoke(
        sign_cli, ["sign", "proj/dev", str(env_file), "--secret", "s", "--sign-dir", sign_dir]
    )
    runner.invoke(
        sign_cli, ["sign", "proj/prod", str(env_file), "--secret", "s", "--sign-dir", sign_dir]
    )
    result = runner.invoke(sign_cli, ["list", "--sign-dir", sign_dir])
    assert "proj/dev" in result.output
    assert "proj/prod" in result.output
