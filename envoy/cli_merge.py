"""CLI commands for merging .env files."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.merge import ConflictStrategy, merge_envs


@click.group("merge")
def merge_cli() -> None:
    """Merge .env files with conflict resolution."""


@merge_cli.command("run")
@click.argument("base", type=click.Path(exists=True, dir_okay=False))
@click.argument("other", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--strategy",
    type=click.Choice([s.value for s in ConflictStrategy], case_sensitive=False),
    default=ConflictStrategy.OURS.value,
    show_default=True,
    help="How to resolve conflicting keys.",
)
@click.option("--output", "-o", type=click.Path(dir_okay=False), default=None,
              help="Write merged result to this file (default: stdout).")
def run(base: str, other: str, strategy: str, output: str | None) -> None:
    """Merge OTHER into BASE and write the result."""
    base_text = Path(base).read_text()
    other_text = Path(other).read_text()

    result = merge_envs(base_text, other_text, ConflictStrategy(strategy))

    if not result.success:
        click.echo(click.style("Conflicts detected:", fg="red"), err=True)
        for c in result.conflicts:
            click.echo(f"  {c.key}: base={c.base_value!r}  other={c.other_value!r}", err=True)
        click.echo("Use --strategy=ours or --strategy=theirs to resolve.", err=True)
        sys.exit(1)

    env_str = result.to_env_string()

    if output:
        Path(output).write_text(env_str)
        click.echo(click.style(f"Written to {output}", fg="green"))
    else:
        click.echo(env_str, nl=False)

    click.echo(click.style(result.summary(), fg="cyan"), err=True)


@merge_cli.command("preview")
@click.argument("base", type=click.Path(exists=True, dir_okay=False))
@click.argument("other", type=click.Path(exists=True, dir_okay=False))
def preview(base: str, other: str) -> None:
    """Show what a merge would produce without writing anything."""
    base_text = Path(base).read_text()
    other_text = Path(other).read_text()

    result_ours = merge_envs(base_text, other_text, ConflictStrategy.OURS)

    if result_ours.added:
        click.echo(click.style("Keys to be added:", fg="green"))
        for k in sorted(result_ours.added):
            click.echo(f"  + {k}")

    result_err = merge_envs(base_text, other_text, ConflictStrategy.ERROR)
    if result_err.conflicts:
        click.echo(click.style("Conflicting keys:", fg="yellow"))
        for c in result_err.conflicts:
            click.echo(f"  ~ {c.key}: {c.base_value!r} -> {c.other_value!r}")

    if not result_ours.added and not result_err.conflicts:
        click.echo(click.style("No changes.", fg="cyan"))
