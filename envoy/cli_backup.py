"""CLI commands for backup / restore of env files."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from envoy.backup import BackupManager


@click.group("backup")
def backup_cli() -> None:
    """Create and restore .env backups."""


def _manager(backup_dir: str) -> BackupManager:
    return BackupManager(Path(backup_dir))


@backup_cli.command("create")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--backup-dir", default=".envoy/backups", show_default=True)
@click.option("--label", default=None, help="Optional label embedded in archive name.")
def create(files: tuple, backup_dir: str, label: Optional[str]) -> None:
    """Archive FILES into a timestamped .tar.gz backup."""
    mgr = _manager(backup_dir)
    sources = [Path(f) for f in files]
    result = mgr.create(sources, label=label)
    if result.success:
        click.echo(f"Backup created: {result.archive}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@backup_cli.command("restore")
@click.argument("archive", type=click.Path(exists=True))
@click.option("--target-dir", default=".", show_default=True)
@click.option("--backup-dir", default=".envoy/backups", show_default=True)
def restore(archive: str, target_dir: str, backup_dir: str) -> None:
    """Extract ARCHIVE into TARGET_DIR."""
    mgr = _manager(backup_dir)
    result = mgr.restore(Path(archive), Path(target_dir))
    if result.success:
        click.echo(f"Restored to: {result.restored_to}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@backup_cli.command("list")
@click.option("--backup-dir", default=".envoy/backups", show_default=True)
def list_backups(backup_dir: str) -> None:
    """List available backup archives."""
    mgr = _manager(backup_dir)
    archives = mgr.list_backups()
    if not archives:
        click.echo("No backups found.")
        return
    for arch in archives:
        click.echo(str(arch))


@backup_cli.command("prune")
@click.option("--keep", default=5, show_default=True, help="Number of recent backups to keep.")
@click.option("--backup-dir", default=".envoy/backups", show_default=True)
def prune(keep: int, backup_dir: str) -> None:
    """Delete old backups, keeping the KEEP most recent."""
    mgr = _manager(backup_dir)
    deleted = mgr.prune(keep=keep)
    if deleted:
        for d in deleted:
            click.echo(f"Deleted: {d}")
        click.echo(f"{len(deleted)} backup(s) pruned.")
    else:
        click.echo("Nothing to prune.")
