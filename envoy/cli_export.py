"""CLI commands for exporting env files to various formats."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.export import export_env, ExportFormat


@click.group(name="export")
def export_cli() -> None:
    """Export .env files to shell, JSON, or Docker format."""


@export_cli.command(name="convert")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["shell", "json", "docker"]),
    default="shell",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False),
    default=None,
    help="Write output to file instead of stdout.",
)
def convert(env_file: str, fmt: str, output: str | None) -> None:
    """Convert ENV_FILE to the requested format."""
    text = Path(env_file).read_text(encoding="utf-8")
    result = export_env(text, fmt=fmt)  # type: ignore[arg-type]

    if output:
        Path(output).write_text(result.content, encoding="utf-8")
        click.echo(f"Exported {result.key_count} key(s) to {output} [{fmt}]")
    else:
        click.echo(result.content)


@export_cli.command(name="summary")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
def summary(env_file: str) -> None:
    """Print a summary of keys defined in ENV_FILE."""
    text = Path(env_file).read_text(encoding="utf-8")
    result = export_env(text, fmt="json")
    import json
    data = json.loads(result.content)
    click.echo(f"File   : {env_file}")
    click.echo(f"Keys   : {result.key_count}")
    for key in data:
        click.echo(f"  - {key}")
