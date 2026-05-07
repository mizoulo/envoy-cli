"""CLI commands for the archive feature."""
from __future__ import annotations

from pathlib import Path

import click

from envoy.archive import ArchiveManager
from envoy.cli import _make_vault


@click.group("archive")
def archive_cli() -> None:
    """Bundle and restore env entries as zip archives."""


@archive_cli.command("create")
@click.argument("project")
@click.argument("dest", type=click.Path())
@click.option("--password", "-p", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True,
              help="Encryption password.")
@click.option("--vault-dir", default=".envoy", show_default=True,
              help="Path to local vault directory.")
def create(project: str, dest: str, password: str, vault_dir: str) -> None:
    """Bundle all envs for PROJECT into a zip archive at DEST."""
    vault = _make_vault(vault_dir)
    mgr = ArchiveManager(vault)
    result = mgr.create(project, Path(dest), password)
    if result.success:
        click.echo(f"Archive created: {result.path}")
        click.echo(f"Entries bundled: {', '.join(result.entries)}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@archive_cli.command("extract")
@click.argument("project")
@click.argument("src", type=click.Path(exists=True))
@click.option("--password", "-p", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True,
              help="Encryption password.")
@click.option("--vault-dir", default=".envoy", show_default=True,
              help="Path to local vault directory.")
def extract(project: str, src: str, password: str, vault_dir: str) -> None:
    """Restore env entries from archive SRC into PROJECT."""
    vault = _make_vault(vault_dir)
    mgr = ArchiveManager(vault)
    result = mgr.extract(project, Path(src), password)
    if result.success:
        click.echo(f"Restored {len(result.entries)} entries from {result.path}")
        for name in result.entries:
            click.echo(f"  - {name}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)
