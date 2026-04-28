"""Entry point and CLI commands for envoy-cli."""

import sys
from pathlib import Path
from typing import Optional

import click

from envoy.config import Config
from envoy.storage import LocalStorage
from envoy.vault import Vault


def _make_vault(config: Config, password: str) -> Vault:
    storage_path = Path(config.get("storage_path"))
    storage = LocalStorage(storage_path)
    return Vault(storage=storage, password=password)


@click.group()
@click.version_option(version="0.1.0", prog_name="envoy")
def cli() -> None:
    """envoy — manage and sync .env files with encrypted remote storage."""


@cli.command()
@click.argument("env_file", type=click.Path(exists=True))
@click.argument("name")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
@click.option("--config", "config_path", default=None, help="Path to config file.")
def push(env_file: str, name: str, password: str, config_path: Optional[str]) -> None:
    """Encrypt and push ENV_FILE to the vault under NAME."""
    config = Config(config_path=config_path)
    vault = _make_vault(config, password)
    path = vault.push(name, Path(env_file).read_text(encoding="utf-8"))
    click.echo(f"Pushed '{name}' → {path}")


@cli.command()
@click.argument("name")
@click.option("--out", "-o", default=".env", show_default=True, help="Output file path.")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
@click.option("--config", "config_path", default=None, help="Path to config file.")
def pull(name: str, out: str, password: str, config_path: Optional[str]) -> None:
    """Pull and decrypt NAME from the vault into OUT."""
    config = Config(config_path=config_path)
    vault = _make_vault(config, password)
    content = vault.pull(name)
    Path(out).write_text(content, encoding="utf-8")
    click.echo(f"Pulled '{name}' → {out}")


@cli.command(name="list")
@click.option("--config", "config_path", default=None, help="Path to config file.")
def list_envs(config_path: Optional[str]) -> None:
    """List all environments stored in the vault."""
    config = Config(config_path=config_path)
    storage = LocalStorage(Path(config.get("storage_path")))
    vault = Vault(storage=storage, password="")
    envs = vault.list_envs()
    if not envs:
        click.echo("No environments found.")
    else:
        for name in envs:
            click.echo(f"  • {name}")


@cli.group()
def config() -> None:
    """View or modify envoy configuration."""


@config.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--config", "config_path", default=None)
def config_set(key: str, value: str, config_path: Optional[str]) -> None:
    """Set a configuration KEY to VALUE."""
    cfg = Config(config_path=config_path)
    cfg.set(key, value)
    click.echo(f"Set {key} = {value}")


@config.command(name="show")
@click.option("--config", "config_path", default=None)
def config_show(config_path: Optional[str]) -> None:
    """Display current configuration."""
    cfg = Config(config_path=config_path)
    for key, val in cfg.as_dict().items():
        click.echo(f"{key}: {val}")


if __name__ == "__main__":
    cli()
