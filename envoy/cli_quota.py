"""CLI commands for quota management."""
from __future__ import annotations

import click
from pathlib import Path
from envoy.quota import QuotaManager, QuotaPolicy


def _manager(quota_dir: str) -> QuotaManager:
    p = Path(quota_dir)
    p.mkdir(parents=True, exist_ok=True)
    return QuotaManager(p / "quotas.json")


@click.group("quota")
def quota_cli() -> None:
    """Manage per-project key quotas."""


@quota_cli.command("set")
@click.argument("project")
@click.option("--max-keys", default=100, show_default=True, help="Maximum number of keys.")
@click.option("--max-value-bytes", default=4096, show_default=True, help="Max value size in bytes.")
@click.option("--max-key-length", default=128, show_default=True, help="Max key name length.")
@click.option("--quota-dir", default=".envoy/quotas", envvar="ENVOY_QUOTA_DIR")
def set_quota(
    project: str,
    max_keys: int,
    max_value_bytes: int,
    max_key_length: int,
    quota_dir: str,
) -> None:
    """Set quota policy for PROJECT."""
    mgr = _manager(quota_dir)
    policy = QuotaPolicy(
        max_keys=max_keys,
        max_value_bytes=max_value_bytes,
        max_key_length=max_key_length,
    )
    mgr.set_policy(project, policy)
    click.echo(f"Quota set for '{project}': max_keys={max_keys}, max_value_bytes={max_value_bytes}, max_key_length={max_key_length}")


@quota_cli.command("show")
@click.argument("project")
@click.option("--quota-dir", default=".envoy/quotas", envvar="ENVOY_QUOTA_DIR")
def show_quota(project: str, quota_dir: str) -> None:
    """Show quota policy for PROJECT."""
    mgr = _manager(quota_dir)
    policy = mgr.get_policy(project)
    click.echo(f"Project : {project}")
    click.echo(f"  max_keys        : {policy.max_keys}")
    click.echo(f"  max_value_bytes : {policy.max_value_bytes}")
    click.echo(f"  max_key_length  : {policy.max_key_length}")


@quota_cli.command("remove")
@click.argument("project")
@click.option("--quota-dir", default=".envoy/quotas", envvar="ENVOY_QUOTA_DIR")
def remove_quota(project: str, quota_dir: str) -> None:
    """Remove quota policy for PROJECT (resets to defaults)."""
    mgr = _manager(quota_dir)
    removed = mgr.remove_policy(project)
    if removed:
        click.echo(f"Quota policy removed for '{project}'.")
    else:
        click.echo(f"No custom quota found for '{project}'.")
