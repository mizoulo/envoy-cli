"""Notification system for envoy-cli events."""
from __future__ import annotations

import json
import smtplib
import urllib.request
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class NotifyResult:
    action: str
    channel: str
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:
        status = "ok" if self.success else f"error={self.error}"
        return f"<NotifyResult action={self.action!r} channel={self.channel!r} {status}>"


@dataclass
class NotifyConfig:
    channel: str  # "webhook" | "email" | "log"
    webhook_url: Optional[str] = None
    email_to: Optional[str] = None
    email_from: str = "envoy@localhost"
    smtp_host: str = "localhost"
    smtp_port: int = 25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel,
            "webhook_url": self.webhook_url,
            "email_to": self.email_to,
            "email_from": self.email_from,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotifyConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class Notifier:
    def __init__(self, config_path: Path) -> None:
        self._path = config_path
        self._configs: List[NotifyConfig] = self._load()

    def _load(self) -> List[NotifyConfig]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text())
        return [NotifyConfig.from_dict(c) for c in raw.get("channels", [])]

    def save(self, cfg: NotifyConfig) -> None:
        existing = {c.channel + str(c.webhook_url) + str(c.email_to): c for c in self._configs}
        key = cfg.channel + str(cfg.webhook_url) + str(cfg.email_to)
        existing[key] = cfg
        self._configs = list(existing.values())
        self._path.write_text(json.dumps({"channels": [c.to_dict() for c in self._configs]}, indent=2))

    def send(self, action: str, message: str) -> List[NotifyResult]:
        results = []
        for cfg in self._configs:
            results.append(self._dispatch(action, message, cfg))
        return results

    def _dispatch(self, action: str, message: str, cfg: NotifyConfig) -> NotifyResult:
        try:
            if cfg.channel == "webhook":
                return self._send_webhook(action, message, cfg)
            elif cfg.channel == "email":
                return self._send_email(action, message, cfg)
            elif cfg.channel == "log":
                return NotifyResult(action=action, channel="log")
            else:
                return NotifyResult(action=action, channel=cfg.channel, error=f"unknown channel: {cfg.channel}")
        except Exception as exc:  # noqa: BLE001
            return NotifyResult(action=action, channel=cfg.channel, error=str(exc))

    def _send_webhook(self, action: str, message: str, cfg: NotifyConfig) -> NotifyResult:
        payload = json.dumps({"action": action, "message": message}).encode()
        req = urllib.request.Request(cfg.webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=5)
        return NotifyResult(action=action, channel="webhook")

    def _send_email(self, action: str, message: str, cfg: NotifyConfig) -> NotifyResult:
        msg = EmailMessage()
        msg["Subject"] = f"[envoy] {action}"
        msg["From"] = cfg.email_from
        msg["To"] = cfg.email_to
        msg.set_content(message)
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as smtp:
            smtp.send_message(msg)
        return NotifyResult(action=action, channel="email")
