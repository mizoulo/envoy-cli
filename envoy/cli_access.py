"""CLI commands for managing access control rules on env keys."""
from __future__ import annotations

from pathlib import Path

import click

from envoy.access import AccessManager

_RULES_FILE = Path(".envoy") / "access_rules.json"


def _manager(rules_path: Path) -> AccessManager:
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    return AccessManager(rules_path)


@click.group("access")
def access_cli() -> None:
    """Manage key-level access control rules."""


@access_cli.command("add")
@click.argument("pattern")
@click.argument("permission", type=click.Choice(["read", "write", "none"]))
@click.option("--note", default="", help="Optional description for this rule.")
@click.option("--rules-file", default=str(_RULES_FILE), show_default=True)
def add(pattern: str, permission: str, note: str, rules_file: str) -> None:
    """Add an access rule for keys matching PATTERN."""
    m = _manager(Path(rules_file))
    rule = m.add_rule(pattern, permission, note)
    click.echo(f"Added rule: {rule.pattern!r} -> {rule.permission}")


@access_cli.command("remove")
@click.argument("pattern")
@click.option("--rules-file", default=str(_RULES_FILE), show_default=True)
def remove(pattern: str, rules_file: str) -> None:
    """Remove the access rule for PATTERN."""
    m = _manager(Path(rules_file))
    if m.remove_rule(pattern):
        click.echo(f"Removed rule for pattern {pattern!r}.")
    else:
        click.echo(f"No rule found for pattern {pattern!r}.", err=True)
        raise SystemExit(1)


@access_cli.command("list")
@click.option("--rules-file", default=str(_RULES_FILE), show_default=True)
def list_rules(rules_file: str) -> None:
    """List all access control rules."""
    m = _manager(Path(rules_file))
    rules = m.list_rules()
    if not rules:
        click.echo("No access rules defined.")
        return
    for rule in rules:
        note_part = f"  # {rule.note}" if rule.note else ""
        click.echo(f"  {rule.pattern:<30} {rule.permission}{note_part}")


@access_cli.command("check")
@click.argument("key")
@click.argument("action", type=click.Choice(["read", "write"]))
@click.option("--rules-file", default=str(_RULES_FILE), show_default=True)
def check(key: str, action: str, rules_file: str) -> None:
    """Check whether ACTION is permitted for KEY."""
    m = _manager(Path(rules_file))
    result = m.check(key, action)
    if result.allowed:
        click.echo(f"ALLOWED: {action} on {key!r}")
    else:
        click.echo(f"DENIED: {action} on {key!r}")
        raise SystemExit(1)
