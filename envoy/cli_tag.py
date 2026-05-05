"""CLI commands for managing env tags."""
import click
from envoy.cli import _make_vault
from envoy.tag import TagManager


@click.group("tag")
def tag_cli():
    """Add, remove, and query tags on vault entries."""


@tag_cli.command("add")
@click.argument("project")
@click.argument("env")
@click.argument("tags", nargs=-1, required=True)
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
def add(project: str, env: str, tags: tuple, password: str) -> None:
    """Add one or more TAGS to a vault entry."""
    vault = _make_vault(password)
    manager = TagManager(vault)
    result = manager.add(project, env, list(tags))
    if not result.success:
        for err in result.errors:
            click.echo(f"error: {err}", err=True)
        raise SystemExit(1)
    if result.added:
        click.echo(f"Added: {', '.join(result.added)}")
    else:
        click.echo("No new tags added (already present).")


@tag_cli.command("remove")
@click.argument("project")
@click.argument("env")
@click.argument("tags", nargs=-1, required=True)
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
def remove(project: str, env: str, tags: tuple, password: str) -> None:
    """Remove one or more TAGS from a vault entry."""
    vault = _make_vault(password)
    manager = TagManager(vault)
    result = manager.remove(project, env, list(tags))
    if not result.success:
        for err in result.errors:
            click.echo(f"error: {err}", err=True)
        raise SystemExit(1)
    if result.removed:
        click.echo(f"Removed: {', '.join(result.removed)}")
    else:
        click.echo("Nothing to remove.")


@tag_cli.command("list")
@click.argument("project")
@click.argument("env")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
def list_tags(project: str, env: str, password: str) -> None:
    """List all tags for a vault entry."""
    vault = _make_vault(password)
    manager = TagManager(vault)
    tags = manager.list_tags(project, env)
    if tags:
        for tag in tags:
            click.echo(tag)
    else:
        click.echo("No tags found.")


@tag_cli.command("find")
@click.argument("project")
@click.argument("tag")
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
def find(project: str, tag: str, password: str) -> None:
    """Find all envs in PROJECT that carry TAG."""
    vault = _make_vault(password)
    manager = TagManager(vault)
    envs = manager.find_by_tag(project, tag)
    if envs:
        for env in envs:
            click.echo(env)
    else:
        click.echo(f"No envs tagged '{tag}' in project '{project}'.")
