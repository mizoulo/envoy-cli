"""CLI commands for snapshot capture and restore."""

from __future__ import annotations

import click

from envoy.cli import _make_vault
from envoy.snapshot import SnapshotManager


@click.group("snapshot")
def snapshot_cli() -> None:
    """Manage .env snapshots."""


@snapshot_cli.command("capture")
@click.argument("project")
@click.argument("env_name")
@click.argument("file", type=click.Path(exists=True))
@click.option("--label", default=None, help="Optional human-readable label.")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option("--vault-dir", default=".envoy_vault", show_default=True)
def capture(project: str, env_name: str, file: str, label, password: str, vault_dir: str) -> None:
    """Capture a snapshot of FILE for PROJECT/ENV_NAME."""
    vault = _make_vault(vault_dir, password)
    manager = SnapshotManager(vault, project)
    content = open(file).read()
    snap = manager.capture(env_name, content, label=label)
    click.echo(f"Snapshot captured: {snap.snapshot_key}")


@snapshot_cli.command("restore")
@click.argument("project")
@click.argument("env_name")
@click.argument("timestamp", type=int)
@click.option("--label", default=None, help="Label used during capture.")
@click.option("--output", "-o", default=".env", show_default=True, help="Output file path.")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option("--vault-dir", default=".envoy_vault", show_default=True)
def restore(project: str, env_name: str, timestamp: int, label, output: str, password: str, vault_dir: str) -> None:
    """Restore a snapshot to OUTPUT file."""
    vault = _make_vault(vault_dir, password)
    manager = SnapshotManager(vault, project)
    content = manager.restore(env_name, timestamp, label=label)
    with open(output, "w") as f:
        f.write(content)
    click.echo(f"Restored snapshot {timestamp} -> {output}")


@snapshot_cli.command("list")
@click.argument("project")
@click.argument("env_name")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option("--vault-dir", default=".envoy_vault", show_default=True)
def list_snapshots(project: str, env_name: str, password: str, vault_dir: str) -> None:
    """List all snapshots for PROJECT/ENV_NAME."""
    vault = _make_vault(vault_dir, password)
    manager = SnapshotManager(vault, project)
    keys = manager.list_snapshots(env_name)
    if not keys:
        click.echo("No snapshots found.")
        return
    for key in sorted(keys):
        click.echo(key)
