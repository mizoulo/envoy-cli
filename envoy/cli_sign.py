"""CLI commands for signing and verifying .env file integrity."""
from __future__ import annotations

from pathlib import Path

import click

from envoy.sign import SignatureStore


def _store(sign_dir: str) -> SignatureStore:
    p = Path(sign_dir)
    p.mkdir(parents=True, exist_ok=True)
    return SignatureStore(p / "signatures.json")


@click.group("sign")
def sign_cli() -> None:
    """Sign and verify .env file integrity using HMAC."""


@sign_cli.command("sign")
@click.argument("key")
@click.argument("file", type=click.Path(exists=True))
@click.option("--secret", envvar="ENVOY_SIGN_SECRET", required=True, help="HMAC secret key")
@click.option("--sign-dir", default=".envoy/signs", show_default=True)
def sign_file(key: str, file: str, secret: str, sign_dir: str) -> None:
    """Sign FILE and record its HMAC under KEY."""
    data = Path(file).read_bytes()
    result = _store(sign_dir).sign(key, data, secret)
    if result.success():
        click.echo(f"Signed {key!r} from {file}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@sign_cli.command("verify")
@click.argument("key")
@click.argument("file", type=click.Path(exists=True))
@click.option("--secret", envvar="ENVOY_SIGN_SECRET", required=True, help="HMAC secret key")
@click.option("--sign-dir", default=".envoy/signs", show_default=True)
def verify_file(key: str, file: str, secret: str, sign_dir: str) -> None:
    """Verify FILE integrity against the stored signature for KEY."""
    data = Path(file).read_bytes()
    result = _store(sign_dir).verify(key, data, secret)
    if result.success():
        click.echo(f"Verified {key!r} — signature matches.")
    else:
        click.echo(f"Verification failed for {key!r}: {result.error}", err=True)
        raise SystemExit(1)


@sign_cli.command("remove")
@click.argument("key")
@click.option("--sign-dir", default=".envoy/signs", show_default=True)
def remove_sig(key: str, sign_dir: str) -> None:
    """Remove the stored signature for KEY."""
    result = _store(sign_dir).remove(key)
    if result.success():
        click.echo(f"Removed signature for {key!r}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        raise SystemExit(1)


@sign_cli.command("list")
@click.option("--sign-dir", default=".envoy/signs", show_default=True)
def list_sigs(sign_dir: str) -> None:
    """List all keys with stored signatures."""
    keys = _store(sign_dir).list_keys()
    if not keys:
        click.echo("No signatures recorded.")
    else:
        for k in sorted(keys):
            click.echo(k)
