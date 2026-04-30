"""CLI commands for comparing .env environments."""
import click
from pathlib import Path

from envoy.compare import compare_envs
from envoy.vault import Vault


@click.group(name="compare")
def compare_cli():
    """Compare .env files across environments or projects."""


@compare_cli.command("envs")
@click.argument("env_a")
@click.argument("env_b")
@click.option("--project", default="default", show_default=True, help="Project name.")
@click.option("--vault-dir", default=".envoy", show_default=True)
@click.option("--password", envvar="ENVOY_PASSWORD", prompt=True, hide_input=True)
@click.option("--show-values", is_flag=True, default=False, help="Unmask differing values.")
def compare_envs_cmd(env_a, env_b, project, vault_dir, password, show_values):
    """Compare two stored environments by name."""
    vault = Vault(vault_dir=vault_dir, password=password)
    try:
        text_a = vault.pull(project=project, env=env_a)
        text_b = vault.pull(project=project, env=env_b)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    result = compare_envs(
        text_a, text_b,
        label_a=env_a,
        label_b=env_b,
        mask_values=not show_values,
    )
    click.echo(result.summary())
    if not result.is_identical:
        raise SystemExit(1)


@compare_cli.command("files")
@click.argument("file_a", type=click.Path(exists=True))
@click.argument("file_b", type=click.Path(exists=True))
@click.option("--show-values", is_flag=True, default=False)
def compare_files(file_a, file_b, show_values):
    """Compare two local .env files directly."""
    text_a = Path(file_a).read_text()
    text_b = Path(file_b).read_text()
    result = compare_envs(
        text_a, text_b,
        label_a=file_a,
        label_b=file_b,
        mask_values=not show_values,
    )
    click.echo(result.summary())
    if not result.is_identical:
        raise SystemExit(1)
