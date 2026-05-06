"""CLI commands for TTL management."""
import click

from envoy.storage import LocalStorage
from envoy.ttl import TTLManager


@click.group("ttl")
def ttl_cli() -> None:
    """Manage time-to-live expiry on stored env entries."""


def _manager(vault_dir: str) -> TTLManager:
    return TTLManager(LocalStorage(vault_dir))


@ttl_cli.command("set")
@click.argument("project")
@click.argument("env")
@click.option("--seconds", "-s", default=3600, show_default=True, help="TTL in seconds.")
@click.option("--vault-dir", default=".envoy", show_default=True, envvar="ENVOY_VAULT_DIR")
def set_ttl(project: str, env: str, seconds: int, vault_dir: str) -> None:
    """Set a TTL expiry on PROJECT/ENV."""
    result = _manager(vault_dir).set_ttl(project, env, seconds)
    if result.success():
        click.echo(f"TTL set for {project}/{env}: expires in {seconds}s")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@ttl_cli.command("clear")
@click.argument("project")
@click.argument("env")
@click.option("--vault-dir", default=".envoy", show_default=True, envvar="ENVOY_VAULT_DIR")
def clear_ttl(project: str, env: str, vault_dir: str) -> None:
    """Remove TTL expiry from PROJECT/ENV."""
    result = _manager(vault_dir).clear_ttl(project, env)
    if result.success():
        click.echo(f"TTL cleared for {project}/{env}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@ttl_cli.command("status")
@click.argument("project")
@click.argument("env")
@click.option("--vault-dir", default=".envoy", show_default=True, envvar="ENVOY_VAULT_DIR")
def status(project: str, env: str, vault_dir: str) -> None:
    """Show TTL status for PROJECT/ENV."""
    mgr = _manager(vault_dir)
    expiry = mgr.get_expiry(project, env)
    if expiry is None:
        click.echo(f"{project}/{env}: no TTL set")
        return
    expired = mgr.is_expired(project, env)
    state = "EXPIRED" if expired else "active"
    click.echo(f"{project}/{env}: {state} (expiry={expiry:.0f})")


@ttl_cli.command("list")
@click.option("--vault-dir", default=".envoy", show_default=True, envvar="ENVOY_VAULT_DIR")
@click.option("--expired-only", is_flag=True, default=False)
def list_ttl(vault_dir: str, expired_only: bool) -> None:
    """List all entries with a TTL."""
    entries = _manager(vault_dir).list_expiring()
    if expired_only:
        entries = [e for e in entries if e["expired"]]
    if not entries:
        click.echo("No TTL entries found.")
        return
    for e in entries:
        state = "EXPIRED" if e["expired"] else f"in {e['remaining']:.0f}s"
        click.echo(f"  {e['key']}: {state}")
