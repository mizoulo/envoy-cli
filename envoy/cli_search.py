"""CLI commands for searching across vault envs."""
from __future__ import annotations

import click

from envoy.cli import _make_vault
from envoy.config import Config
from envoy.search import EnvSearcher


@click.group(name="search")
def search_cli() -> None:
    """Search across stored .env files."""


@search_cli.command(name="grep")
@click.argument("pattern")
@click.option("--project", "-p", required=True, help="Project name to search within.")
@click.option("--keys-only", is_flag=True, default=False, help="Match against keys only.")
@click.option("--ignore-case", "-i", is_flag=True, default=False, help="Case-insensitive search.")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
def grep(
    pattern: str,
    project: str,
    keys_only: bool,
    ignore_case: bool,
    password: str,
) -> None:
    """Search for PATTERN in all envs of PROJECT."""
    vault = _make_vault()
    searcher = EnvSearcher(vault, password)
    result = searcher.search(pattern, project, keys_only=keys_only, ignore_case=ignore_case)

    if not result.found:
        click.echo(result.summary())
        return

    for match in result.matches:
        click.echo(repr(match))

    click.echo(f"\n{result.summary()}")


@search_cli.command(name="list-keys")
@click.option("--project", "-p", required=True, help="Project name.")
@click.option("--env", "-e", required=True, help="Environment name.")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
def list_keys(project: str, env: str, password: str) -> None:
    """List all keys defined in a specific env file."""
    vault = _make_vault()
    try:
        content = vault.pull(project, env, password)
    except FileNotFoundError:
        click.echo(f"Error: env '{env}' not found in project '{project}'.", err=True)
        raise SystemExit(1)

    keys = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key = line.split("=", 1)[0]
        keys.append(key)

    if not keys:
        click.echo("No keys found.")
        return

    for key in keys:
        click.echo(key)
