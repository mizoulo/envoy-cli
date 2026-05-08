"""CLI commands for variable resolution."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.resolve import resolve_env


@click.group("resolve")
def resolve_cli() -> None:
    """Expand ${VAR} references inside .env files."""


@resolve_cli.command("show")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--only-changed", is_flag=True, default=False,
              help="Print only keys whose value changed after resolution.")
def show(env_file: str, only_changed: bool) -> None:
    """Resolve and print all variables from ENV_FILE."""
    text = Path(env_file).read_text()
    result = resolve_env(text)

    if result.cycles:
        click.echo(f"[error] Circular references detected: {', '.join(result.cycles)}",
                   err=True)
        sys.exit(1)

    # Rebuild raw values for comparison
    raw: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        raw[k.strip()] = v.strip().strip('"').strip("'")

    for key, value in sorted(result.resolved.items()):
        original = raw.get(key, "")
        if only_changed and value == original:
            continue
        marker = " *" if value != original else ""
        click.echo(f"{key}={value}{marker}")

    if result.unresolved:
        click.echo(f"\n[warn] Unresolved references in: {', '.join(result.unresolved)}",
                   err=True)


@resolve_cli.command("check")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
def check(env_file: str) -> None:
    """Check ENV_FILE for unresolved or circular references."""
    text = Path(env_file).read_text()
    result = resolve_env(text)

    if result.cycles:
        click.echo(f"[error] Circular references: {', '.join(result.cycles)}")
        sys.exit(1)

    if result.unresolved:
        click.echo(f"[warn]  Unresolved variables: {', '.join(result.unresolved)}")
        sys.exit(2)

    click.echo("[ok] All references resolved successfully.")
