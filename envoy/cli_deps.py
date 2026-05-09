"""CLI commands for dependency tracking."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.deps import DepGraph

_DEFAULT_INDEX = Path(".envoy") / "deps.json"


def _graph(index: str) -> DepGraph:
    return DepGraph(_index_path=Path(index))


@click.group("deps")
def deps_cli() -> None:
    """Track and validate .env file dependencies."""


@deps_cli.command("record")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--index", default=str(_DEFAULT_INDEX), show_default=True)
def record(env_file: str, index: str) -> None:
    """Index external variable references in ENV_FILE."""
    text = Path(env_file).read_text()
    g = _graph(index)
    g.record(env_file, text)
    click.echo(f"Recorded deps for {env_file}")
    deps = g.all_deps().get(env_file, [])
    if deps:
        click.echo("  External refs: " + ", ".join(deps))
    else:
        click.echo("  No external refs found.")


@deps_cli.command("check")
@click.argument("env_file")
@click.argument("provider_file", type=click.Path(exists=True))
@click.option("--index", default=str(_DEFAULT_INDEX), show_default=True)
def check(env_file: str, provider_file: str, index: str) -> None:
    """Check whether PROVIDER_FILE satisfies deps of ENV_FILE."""
    provider_text = Path(provider_file).read_text()
    g = _graph(index)
    result = g.check(env_file, provider_text)
    if result.satisfied:
        click.echo("Satisfied: " + ", ".join(result.satisfied))
    if result.missing:
        click.secho("Missing:   " + ", ".join(result.missing), fg="red")
        sys.exit(1)
    else:
        click.secho("All dependencies satisfied.", fg="green")


@deps_cli.command("list")
@click.option("--index", default=str(_DEFAULT_INDEX), show_default=True)
def list_deps(index: str) -> None:
    """List all recorded dependency entries."""
    g = _graph(index)
    graph = g.all_deps()
    if not graph:
        click.echo("No dependency records found.")
        return
    for path, refs in sorted(graph.items()):
        ref_str = ", ".join(refs) if refs else "(none)"
        click.echo(f"{path}: {ref_str}")
