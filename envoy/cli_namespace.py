"""CLI commands for namespace management."""
from __future__ import annotations

import click

from envoy.cli import _make_vault
from envoy.namespace import NamespaceManager


@click.group("namespace")
def namespace_cli() -> None:
    """Manage namespaced env files within a project."""


@namespace_cli.command("push")
@click.argument("namespace")
@click.argument("env")
@click.argument("file", type=click.Path(exists=True))
@click.option("--project", required=True, envvar="ENVOY_PROJECT", help="Project name.")
@click.option("--storage-dir", default=".envoy", show_default=True)
@click.option("--password", required=True, envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
def push(namespace: str, env: str, file: str, project: str, storage_dir: str, password: str) -> None:
    """Encrypt and push FILE into NAMESPACE/ENV."""
    vault = _make_vault(project, storage_dir)
    manager = NamespaceManager(vault)
    content = click.open_file(file).read()
    result = manager.push(namespace, env, content, password)
    if result.success:
        click.echo(f"Pushed {namespace}/{env}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@namespace_cli.command("pull")
@click.argument("namespace")
@click.argument("env")
@click.option("--project", required=True, envvar="ENVOY_PROJECT")
@click.option("--storage-dir", default=".envoy", show_default=True)
@click.option("--password", required=True, envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option("--output", "-o", default="-", help="Output file (default: stdout).")
def pull(namespace: str, env: str, project: str, storage_dir: str, password: str, output: str) -> None:
    """Decrypt and pull NAMESPACE/ENV."""
    vault = _make_vault(project, storage_dir)
    manager = NamespaceManager(vault)
    content = manager.pull(namespace, env, password)
    if output == "-":
        click.echo(content)
    else:
        with open(output, "w") as fh:
            fh.write(content)
        click.echo(f"Written to {output}")


@namespace_cli.command("list")
@click.argument("namespace")
@click.option("--project", required=True, envvar="ENVOY_PROJECT")
@click.option("--storage-dir", default=".envoy", show_default=True)
def list_envs(namespace: str, project: str, storage_dir: str) -> None:
    """List all envs stored under NAMESPACE."""
    vault = _make_vault(project, storage_dir)
    manager = NamespaceManager(vault)
    envs = manager.list_envs(namespace)
    if not envs:
        click.echo(f"No envs found in namespace '{namespace}'.")
    else:
        for e in sorted(envs):
            click.echo(e)


@namespace_cli.command("namespaces")
@click.option("--project", required=True, envvar="ENVOY_PROJECT")
@click.option("--storage-dir", default=".envoy", show_default=True)
def list_namespaces(project: str, storage_dir: str) -> None:
    """List all namespaces present in the vault."""
    vault = _make_vault(project, storage_dir)
    manager = NamespaceManager(vault)
    namespaces = manager.list_namespaces()
    if not namespaces:
        click.echo("No namespaces found.")
    else:
        for ns in sorted(namespaces):
            click.echo(ns)
