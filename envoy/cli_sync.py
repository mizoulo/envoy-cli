"""CLI commands for sync and diff operations."""

from __future__ import annotations

from pathlib import Path

import click

from envoy.cli import _make_vault
from envoy.config import Config
from envoy.sync import SyncEngine
from envoy.diff import diff_env_file_vs_bytes


@click.group()
def sync_cli() -> None:
    """Sync and diff commands for envoy."""


@sync_cli.command("push-all")
@click.option("--dir", "base_dir", default=".", show_default=True, help="Directory containing .env.* files.")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option("--storage", default="~/.envoy/vault", show_default=True)
def push_all(base_dir: str, password: str, storage: str) -> None:
    """Push all .env.<name> files in DIR to the vault."""
    vault = _make_vault(storage, password)
    config = Config()
    engine = SyncEngine(vault=vault, config=config)
    results = engine.sync_all("push", Path(base_dir).expanduser())
    for r in results:
        icon = "✓" if r.success else "✗"
        click.echo(f"  {icon} {r.env_name}: {r.message}")


@sync_cli.command("pull-all")
@click.option("--dir", "base_dir", default=".", show_default=True, help="Destination directory.")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option("--storage", default="~/.envoy/vault", show_default=True)
def pull_all(base_dir: str, password: str, storage: str) -> None:
    """Pull all envs from the vault into DIR as .env.<name> files."""
    vault = _make_vault(storage, password)
    config = Config()
    engine = SyncEngine(vault=vault, config=config)
    results = engine.sync_all("pull", Path(base_dir).expanduser())
    for r in results:
        icon = "✓" if r.success else "✗"
        click.echo(f"  {icon} {r.env_name}: {r.message}")


@sync_cli.command("diff")
@click.argument("env_name")
@click.option("--file", "env_file", default=None, help="Local .env file to compare (default: .env.<name>).")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option("--storage", default="~/.envoy/vault", show_default=True)
def diff_cmd(env_name: str, env_file: str | None, password: str, storage: str) -> None:
    """Show diff between a local .env file and the vault version."""
    vault = _make_vault(storage, password)
    try:
        vault_bytes = vault.pull(env_name)
    except KeyError:
        click.echo(f"Error: env {env_name!r} not found in vault.", err=True)
        raise SystemExit(1)
    local_path = Path(env_file) if env_file else Path(f".env.{env_name}")
    diff = diff_env_file_vs_bytes(local_path, vault_bytes)
    if diff.is_clean:
        click.echo("No differences found.")
    else:
        for line in diff.summary_lines():
            click.echo(line)
