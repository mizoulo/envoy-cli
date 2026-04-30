"""CLI commands for the watch feature."""

from __future__ import annotations

import click
from pathlib import Path

from envoy.watch import EnvWatcher, WatchEvent
from envoy.sync import SyncEngine
from envoy.config import Config
from envoy.vault import Vault


def _make_engine(vault_dir: str) -> SyncEngine:
    config = Config()
    vault = Vault(Path(vault_dir), password=config.get("password", ""))
    return SyncEngine(vault, config)


@click.group(name="watch")
def watch_cli() -> None:
    """Watch .env files and auto-sync on change."""


@watch_cli.command()
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--project", "-p", required=True, help="Project name.")
@click.option("--env", "-e", "env_name", required=True, help="Environment name.")
@click.option("--vault-dir", default=".envoy", show_default=True)
@click.option("--interval", default=2.0, show_default=True, help="Poll interval in seconds.")
@click.option("--dry-run", is_flag=True, help="Print changes without pushing.")
def start(
    env_file: str,
    project: str,
    env_name: str,
    vault_dir: str,
    interval: float,
    dry_run: bool,
) -> None:
    """Watch ENV_FILE and push to vault on every change."""
    path = Path(env_file)
    watcher = EnvWatcher(interval=interval)
    watcher.add(path, project, env_name)

    if not dry_run:
        engine = _make_engine(vault_dir)

    def _handle(event: WatchEvent) -> None:
        click.echo(f"[watch] Change detected: {event}")
        if dry_run:
            click.echo("[watch] Dry-run — skipping push.")
            return
        result = engine.push_file(path, project, env_name)
        if result.success:
            click.echo(f"[watch] Pushed {project}/{env_name} successfully.")
        else:
            click.echo(f"[watch] Push failed: {result.message}", err=True)

    watcher.on_change(_handle)
    click.echo(f"[watch] Watching {path} (interval={interval}s) — Ctrl+C to stop.")
    try:
        watcher.run()
    except KeyboardInterrupt:
        click.echo("\n[watch] Stopped.")


@watch_cli.command(name="list")
@click.option("--vault-dir", default=".envoy", show_default=True)
def list_watched(vault_dir: str) -> None:
    """List all registered watch targets from config."""
    config = Config()
    targets = config.get("watch_targets", [])
    if not targets:
        click.echo("No watch targets configured.")
        return
    for t in targets:
        click.echo(f"  {t['path']}  →  {t['project']}/{t['env']}")
