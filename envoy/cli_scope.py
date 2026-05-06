"""CLI commands for scope-based env management."""
import click
from pathlib import Path

from envoy.cli import _make_vault
from envoy.scope import ScopeManager


@click.group("scope")
def scope_cli() -> None:
    """Manage envs within a named scope."""


@scope_cli.command("push")
@click.argument("project")
@click.argument("scope")
@click.argument("env")
@click.argument("file", type=click.Path(exists=True))
@click.password_option("--password", envvar="ENVOY_PASSWORD", prompt=True)
@click.option("--vault-dir", default=".envoy", show_default=True)
def push(project: str, scope: str, env: str, file: str, password: str, vault_dir: str) -> None:
    """Push FILE into SCOPE/ENV for PROJECT."""
    content = Path(file).read_text()
    vault = _make_vault(vault_dir)
    mgr = ScopeManager(vault, scope)
    result = mgr.push(project, env, content, password)
    if result.success:
        click.echo(f"Pushed {project}/{scope}/{env}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@scope_cli.command("pull")
@click.argument("project")
@click.argument("scope")
@click.argument("env")
@click.option("--output", "-o", default="-", help="Output file (default: stdout)")
@click.password_option("--password", envvar="ENVOY_PASSWORD", prompt=True, confirmation_prompt=False)
@click.option("--vault-dir", default=".envoy", show_default=True)
def pull(project: str, scope: str, env: str, output: str, password: str, vault_dir: str) -> None:
    """Pull SCOPE/ENV for PROJECT."""
    vault = _make_vault(vault_dir)
    mgr = ScopeManager(vault, scope)
    result, content = mgr.pull(project, env, password)
    if not result.success:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)
    if output == "-":
        click.echo(content)
    else:
        Path(output).write_text(content)
        click.echo(f"Written to {output}")


@scope_cli.command("list")
@click.argument("project")
@click.argument("scope")
@click.option("--vault-dir", default=".envoy", show_default=True)
def list_envs(project: str, scope: str, vault_dir: str) -> None:
    """List envs within SCOPE for PROJECT."""
    vault = _make_vault(vault_dir)
    mgr = ScopeManager(vault, scope)
    envs = mgr.list_envs(project)
    if not envs:
        click.echo("No envs found.")
    for e in envs:
        click.echo(e)


@scope_cli.command("list-scopes")
@click.argument("project")
@click.option("--vault-dir", default=".envoy", show_default=True)
def list_scopes(project: str, vault_dir: str) -> None:
    """List all scopes that exist for PROJECT."""
    vault = _make_vault(vault_dir)
    mgr = ScopeManager(vault, "_")
    scopes = mgr.list_scopes(project)
    if not scopes:
        click.echo("No scopes found.")
    for s in scopes:
        click.echo(s)
