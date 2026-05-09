"""CLI commands for managing env-key expiration."""
from __future__ import annotations

from pathlib import Path

import click

from envoy.expire import ExpireManager


def _manager(store_dir: str) -> ExpireManager:
    return ExpireManager(Path(store_dir))


@click.group(name="expire")
def expire_cli() -> None:
    """Manage expiration timestamps for vault keys."""


@expire_cli.command(name="set")
@click.argument("key")
@click.argument("ttl", type=float)
@click.option("--store", default=".envoy/expire", show_default=True, help="Expiry store path.")
def set_expiry(key: str, ttl: float, store: str) -> None:
    """Set KEY to expire after TTL seconds from now."""
    result = _manager(store).set_expiry(key, ttl)
    if result.success():
        click.echo(f"Expiry set: {key} expires in {ttl:.0f}s")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@expire_cli.command(name="clear")
@click.argument("key")
@click.option("--store", default=".envoy/expire", show_default=True)
def clear_expiry(key: str, store: str) -> None:
    """Remove expiration for KEY."""
    result = _manager(store).clear_expiry(key)
    if result.success():
        click.echo(f"Expiry cleared for {key}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@expire_cli.command(name="status")
@click.argument("key")
@click.option("--store", default=".envoy/expire", show_default=True)
def status(key: str, store: str) -> None:
    """Show expiration status for KEY."""
    mgr = _manager(store)
    exp = mgr.expiry_time(key)
    if exp is None:
        click.echo(f"{key}: no expiry set")
        return
    expired = mgr.is_expired(key)
    state = "EXPIRED" if expired else "active"
    click.echo(f"{key}: {state} (expires at {exp:.2f})")


@expire_cli.command(name="list-expired")
@click.option("--store", default=".envoy/expire", show_default=True)
def list_expired(store: str) -> None:
    """List all keys whose expiry has passed."""
    keys = _manager(store).expired_keys()
    if not keys:
        click.echo("No expired keys.")
    else:
        for k in keys:
            click.echo(k)
