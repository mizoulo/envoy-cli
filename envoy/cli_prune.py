"""CLI commands for pruning stale env entries."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click

from envoy.vault import Vault
from envoy.prune import prune_project


@click.group("prune")
def prune_cli() -> None:  # pragma: no cover
    """Prune stale env entries from a project."""


def _make_vault(vault_dir: str, password: str) -> Vault:
    return Vault(storage_dir=vault_dir, password=password)


@prune_cli.command("run")
@click.argument("project")
@click.option("--vault-dir", default=".envoy", show_default=True, help="Vault storage directory.")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option(
    "--before",
    default=None,
    metavar="ISO_DATE",
    help="Remove entries older than this ISO-8601 date (e.g. 2024-01-01).",
)
@click.option("--dry-run", is_flag=True, default=False, help="Preview without deleting.")
def run(
    project: str,
    vault_dir: str,
    password: str,
    before: Optional[str],
    dry_run: bool,
) -> None:
    """Prune env entries for PROJECT."""
    cutoff: Optional[datetime] = None
    if before:
        try:
            cutoff = datetime.fromisoformat(before).replace(tzinfo=timezone.utc)
        except ValueError:
            raise click.BadParameter(f"Invalid date format: {before!r}", param_hint="--before")

    vault = _make_vault(vault_dir, password)
    result = prune_project(vault, project, before=cutoff, dry_run=dry_run)

    if not result.success:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)

    tag = "[dry-run] would remove" if dry_run else "Removed"
    if result.removed:
        for name in result.removed:
            click.echo(f"{tag}: {project}/{name}")
    else:
        click.echo("Nothing to prune.")

    if result.skipped:
        click.echo(f"Skipped {len(result.skipped)} fresh entry/entries.")


@prune_cli.command("preview")
@click.argument("project")
@click.option("--vault-dir", default=".envoy", show_default=True)
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option("--before", default=None, metavar="ISO_DATE")
def preview(project: str, vault_dir: str, password: str, before: Optional[str]) -> None:
    """Preview which entries would be pruned (alias for --dry-run)."""
    ctx = click.get_current_context()
    ctx.invoke(run, project=project, vault_dir=vault_dir, password=password, before=before, dry_run=True)
