"""Tests for envoy.cli_scope."""
import pytest
from pathlib import Path
from click.testing import CliRunner

from envoy.cli_scope import scope_cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    d = tmp_path / "vault"
    d.mkdir()
    return d


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("DB_URL=postgres://localhost/dev\nDEBUG=true\n")
    return f


def _push(runner: CliRunner, vault_dir: Path, env_file: Path,
          scope: str = "team-a", env: str = "dev",
          password: str = "secret") -> None:
    """Helper to invoke a push command without repeating boilerplate."""
    runner.invoke(
        scope_cli,
        ["push", "myapp", scope, env, str(env_file),
         "--password", password, "--vault-dir", str(vault_dir)],
    )


def test_push_outputs_confirmation(runner, vault_dir, env_file):
    result = runner.invoke(
        scope_cli,
        ["push", "myapp", "team-a", "dev", str(env_file),
         "--password", "secret", "--vault-dir", str(vault_dir)],
    )
    assert result.exit_code == 0
    assert "myapp/team-a/dev" in result.output


def test_pull_round_trip_stdout(runner, vault_dir, env_file):
    _push(runner, vault_dir, env_file)
    result = runner.invoke(
        scope_cli,
        ["pull", "myapp", "team-a", "dev",
         "--password", "secret", "--vault-dir", str(vault_dir)],
    )
    assert result.exit_code == 0
    assert "DB_URL" in result.output


def test_pull_wrong_password_exits_nonzero(runner, vault_dir, env_file):
    _push(runner, vault_dir, env_file)
    result = runner.invoke(
        scope_cli,
        ["pull", "myapp", "team-a", "dev",
         "--password", "wrong", "--vault-dir", str(vault_dir)],
    )
    assert result.exit_code != 0


def test_list_envs_empty(runner, vault_dir):
    result = runner.invoke(
        scope_cli,
        ["list", "myapp", "team-a", "--vault-dir", str(vault_dir)],
    )
    assert result.exit_code == 0
    assert "No envs found" in result.output


def test_list_envs_after_push(runner, vault_dir, env_file):
    _push(runner, vault_dir, env_file, env="staging")
    result = runner.invoke(
        scope_cli,
        ["list", "myapp", "team-a", "--vault-dir", str(vault_dir)],
    )
    assert result.exit_code == 0
    assert "staging" in result.output


def test_list_scopes_after_push(runner, vault_dir, env_file):
    _push(runner, vault_dir, env_file, scope="team-b", env="prod")
    result = runner.invoke(
        scope_cli,
        ["list-scopes", "myapp", "--vault-dir", str(vault_dir)],
    )
    assert result.exit_code == 0
    assert "team-b" in result.output
