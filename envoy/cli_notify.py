"""CLI commands for managing envoy notifications."""
from __future__ import annotations

from pathlib import Path

import click

from envoy.notify import NotifyConfig, Notifier


def _notifier(ctx: click.Context) -> Notifier:
    cfg_dir = Path(ctx.obj.get("config_dir", ".envoy")) if ctx.obj else Path(".envoy")
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return Notifier(cfg_dir / "notify.json")


@click.group("notify")
def notify_cli() -> None:
    """Manage event notifications (webhooks, email, log)."""


@notify_cli.command("add-webhook")
@click.argument("url")
@click.pass_context
def add_webhook(ctx: click.Context, url: str) -> None:
    """Register a webhook URL for push/pull events."""
    n = _notifier(ctx)
    n.save(NotifyConfig(channel="webhook", webhook_url=url))
    click.echo(f"Webhook registered: {url}")


@notify_cli.command("add-email")
@click.argument("to_addr")
@click.option("--from", "from_addr", default="envoy@localhost", show_default=True)
@click.option("--smtp-host", default="localhost", show_default=True)
@click.option("--smtp-port", default=25, show_default=True)
@click.pass_context
def add_email(
    ctx: click.Context,
    to_addr: str,
    from_addr: str,
    smtp_host: str,
    smtp_port: int,
) -> None:
    """Register an email recipient for event notifications."""
    n = _notifier(ctx)
    n.save(
        NotifyConfig(
            channel="email",
            email_to=to_addr,
            email_from=from_addr,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
        )
    )
    click.echo(f"Email notification registered: {to_addr}")


@notify_cli.command("add-log")
@click.pass_context
def add_log(ctx: click.Context) -> None:
    """Enable log-only notifications (no external calls)."""
    n = _notifier(ctx)
    n.save(NotifyConfig(channel="log"))
    click.echo("Log channel registered.")


@notify_cli.command("list")
@click.pass_context
def list_channels(ctx: click.Context) -> None:
    """List all registered notification channels."""
    n = _notifier(ctx)
    if not n._configs:
        click.echo("No notification channels configured.")
        return
    for cfg in n._configs:
        if cfg.channel == "webhook":
            click.echo(f"  webhook  {cfg.webhook_url}")
        elif cfg.channel == "email":
            click.echo(f"  email    {cfg.email_to}  (smtp={cfg.smtp_host}:{cfg.smtp_port})")
        else:
            click.echo(f"  {cfg.channel}")


@notify_cli.command("test")
@click.option("--action", default="test", show_default=True)
@click.option("--message", default="envoy notification test", show_default=True)
@click.pass_context
def test_notify(ctx: click.Context, action: str, message: str) -> None:
    """Send a test notification to all configured channels."""
    n = _notifier(ctx)
    results = n.send(action, message)
    for r in results:
        status = "OK" if r.success else f"FAIL ({r.error})"
        click.echo(f"  [{r.channel}] {status}")
    if not results:
        click.echo("No channels configured.")
