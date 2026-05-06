"""CLI commands for replaying historical push/pull operations."""

from __future__ import annotations

import click
from pathlib import Path

from envoy.vault import Vault
from envoy.storage import LocalStorage
from envoy.audit import AuditLog
from envoy.replay import ReplayEngine


def _make_engine(vault_dir: str, audit_file: str) -> ReplayEngine:
    storage = LocalStorage(Path(vault_dir))
    vault = Vault(storage=storage, default_password="")
    log = AuditLog(Path(audit_file))
    return ReplayEngine(vault=vault, audit_log=log)


@click.group(name="replay")
def replay_cli() -> None:
    """Replay historical push/pull operations from the audit log."""


@replay_cli.command("push")
@click.argument("project")
@click.argument("env")
@click.option("--content", required=True, help="Env file content to re-push.")
@click.option("--password", prompt=True, hide_input=True, help="Encryption password.")
@click.option("--vault-dir", default=".envoy/vault", show_default=True)
@click.option("--audit-file", default=".envoy/audit.json", show_default=True)
def push(project: str, env: str, content: str, password: str, vault_dir: str, audit_file: str) -> None:
    """Re-push an env file as a replay operation."""
    engine = _make_engine(vault_dir, audit_file)
    engine.vault.default_password = password
    result = engine.replay_push(project, env, content, password)
    if result.success():
        click.echo(f"Replayed push: {project}/{env}")
    else:
        click.echo(f"Replay failed: {result.error}", err=True)
        raise SystemExit(1)


@replay_cli.command("pull")
@click.argument("project")
@click.argument("env")
@click.option("--password", prompt=True, hide_input=True, help="Encryption password.")
@click.option("--vault-dir", default=".envoy/vault", show_default=True)
@click.option("--audit-file", default=".envoy/audit.json", show_default=True)
def pull(project: str, env: str, password: str, vault_dir: str, audit_file: str) -> None:
    """Re-pull an env file as a replay operation."""
    engine = _make_engine(vault_dir, audit_file)
    result = engine.replay_pull(project, env, password)
    if result.success():
        click.echo(f"Replayed pull: {project}/{env}")
    else:
        click.echo(f"Replay failed: {result.error}", err=True)
        raise SystemExit(1)


@replay_cli.command("last")
@click.argument("project")
@click.argument("env")
@click.option("--action", default="replay_push", show_default=True, help="Action to look up.")
@click.option("--audit-file", default=".envoy/audit.json", show_default=True)
def last(project: str, env: str, action: str, audit_file: str) -> None:
    """Show the most recent replay audit entry for a project/env."""
    log = AuditLog(Path(audit_file))
    engine = ReplayEngine(vault=None, audit_log=log)  # type: ignore[arg-type]
    entry = engine.last_entry(project, env, action)
    if entry is None:
        click.echo(f"No entry found for {project}/{env} action={action}")
    else:
        click.echo(f"Last {action} for {project}/{env}: {entry.get('timestamp', 'unknown')}")
