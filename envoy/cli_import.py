"""CLI commands for importing env files into the vault."""
from __future__ import annotations

import click

from envoy.cli import _make_vault
from envoy.import_env import import_env


@click.group(name="import")
def import_cli() -> None:
    """Import .env variables from external files."""


@import_cli.command("run")
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.option("--project", "-p", required=True, help="Target project name.")
@click.option("--env", "-e", default="default", show_default=True, help="Environment name.")
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["dotenv", "json", "shell"]),
    default="dotenv",
    show_default=True,
    help="Source file format.",
)
@click.option(
    "--skip-existing", is_flag=True, default=False,
    help="Skip keys that already exist in the vault.",
)
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def run(
    source: str,
    project: str,
    env: str,
    fmt: str,
    skip_existing: bool,
    password: str,
) -> None:
    """Import variables from SOURCE into the vault."""
    vault = _make_vault(password)

    existing_keys: list[str] = []
    if skip_existing:
        try:
            current = vault.pull(project, env)
            from envoy.import_env import _parse_dotenv
            existing_keys = list(_parse_dotenv(current).keys())
        except Exception:
            pass

    pairs, result = import_env(source, fmt=fmt, skip_existing=skip_existing, existing_keys=existing_keys)

    if not result.success:
        for err in result.errors:
            click.echo(f"  error: {err}", err=True)
        raise SystemExit(1)

    # Merge with existing content if skip_existing
    existing_content = ""
    if skip_existing:
        try:
            existing_content = vault.pull(project, env)
        except Exception:
            pass

    new_lines = [f"{k}={v}" for k, v in pairs.items()]
    merged = "\n".join(filter(None, [existing_content.strip()] + new_lines)) + "\n"
    path = vault.push(project, env, merged)

    click.echo(f"Imported {result.imported} key(s) into {project}/{env} (skipped {result.skipped}).")
    click.echo(f"Stored at: {path}")


@import_cli.command("preview")
@click.argument("source", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["dotenv", "json", "shell"]),
    default="dotenv",
    show_default=True,
)
def preview(source: str, fmt: str) -> None:
    """Preview what would be imported from SOURCE without writing."""
    pairs, result = import_env(source, fmt=fmt)
    if not pairs:
        click.echo("No variables found.")
        return
    click.echo(f"Would import {result.imported} key(s) from {source!r} [{fmt}]:")
    for k, v in pairs.items():
        click.echo(f"  {k}={v}")
