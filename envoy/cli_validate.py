"""CLI commands for .env validation against a schema."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.validate import validate_env


@click.group(name="validate")
def validate_cli() -> None:
    """Validate .env files against a schema."""


@validate_cli.command("check")
@click.argument("env_file", type=click.Path(exists=True))
@click.argument("schema_file", type=click.Path(exists=True))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Disallow keys not declared in the schema.",
)
def check(env_file: str, schema_file: str, strict: bool) -> None:
    """Check ENV_FILE against SCHEMA_FILE."""
    env_text = Path(env_file).read_text()
    schema_text = Path(schema_file).read_text()
    result = validate_env(env_text, schema_text, allow_extra=not strict)

    click.echo(result.summary())
    if not result.valid:
        sys.exit(1)


@validate_cli.command("show-schema")
@click.argument("schema_file", type=click.Path(exists=True))
def show_schema(schema_file: str) -> None:
    """Display annotated schema information."""
    lines = Path(schema_file).read_text().splitlines()
    click.echo(f"Schema: {schema_file}")
    click.echo("-" * 40)
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, _, spec = stripped.partition("=")
            key = key.strip()
            optional = spec.strip().startswith("?")
            tag = click.style("optional", fg="yellow") if optional else click.style("required", fg="red")
            click.echo(f"  {key:30s} [{tag}]")
