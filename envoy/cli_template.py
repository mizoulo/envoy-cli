"""CLI commands for template rendering."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from envoy.template import collect_placeholders, render_template_file


@click.group("template")
def template_cli() -> None:
    """Render and inspect .env template files."""


@template_cli.command("render")
@click.argument("template_file", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None, help="Output file (default: stdout)")
@click.option("-v", "--var", "variables", multiple=True, metavar="KEY=VALUE", help="Variable substitution (repeatable)")
@click.option("--env-file", type=click.Path(exists=True, path_type=Path), default=None, help="Load variables from an existing .env file")
def render(
    template_file: Path,
    output: Optional[Path],
    variables: tuple,
    env_file: Optional[Path],
) -> None:
    """Render TEMPLATE_FILE by substituting {{VAR}} placeholders."""
    vars_dict: dict = {}

    if env_file:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            vars_dict[k.strip()] = v.strip()

    for item in variables:
        if "=" not in item:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {item!r}", param_hint="--var")
        k, _, v = item.partition("=")
        vars_dict[k.strip()] = v.strip()

    result = render_template_file(template_file, vars_dict, output_path=output)

    if output is None:
        click.echo(result.output, nl=False)
    else:
        click.echo(f"Written to {output}")

    if result.missing:
        click.secho(f"Warning: unresolved placeholders: {', '.join(result.missing)}", fg="yellow", err=True)


@template_cli.command("inspect")
@click.argument("template_file", type=click.Path(exists=True, path_type=Path))
def inspect(template_file: Path) -> None:
    """List all {{VAR}} placeholders found in TEMPLATE_FILE."""
    content = template_file.read_text(encoding="utf-8")
    placeholders = collect_placeholders(content)
    if not placeholders:
        click.echo("No placeholders found.")
        return
    click.echo(f"Found {len(placeholders)} placeholder(s):")
    for name in placeholders:
        click.echo(f"  - {name}")
