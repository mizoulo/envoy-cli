"""Tests for envoy.notify."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envoy.notify import NotifyConfig, NotifyResult, Notifier


@pytest.fixture
def cfg_path(tmp_path: Path) -> Path:
    return tmp_path / "notify.json"


@pytest.fixture
def notifier(cfg_path: Path) -> Notifier:
    return Notifier(cfg_path)


def test_notify_result_success_when_no_error():
    r = NotifyResult(action="push", channel="log")
    assert r.success is True


def test_notify_result_failure_when_error():
    r = NotifyResult(action="push", channel="webhook", error="timeout")
    assert r.success is False


def test_notify_result_repr_contains_action_and_channel():
    r = NotifyResult(action="pull", channel="email")
    assert "pull" in repr(r)
    assert "email" in repr(r)


def test_config_round_trip():
    cfg = NotifyConfig(channel="webhook", webhook_url="http://example.com/hook")
    restored = NotifyConfig.from_dict(cfg.to_dict())
    assert restored.channel == "webhook"
    assert restored.webhook_url == "http://example.com/hook"


def test_notifier_starts_empty(notifier: Notifier):
    assert notifier._configs == []


def test_save_persists_config(cfg_path: Path, notifier: Notifier):
    cfg = NotifyConfig(channel="log")
    notifier.save(cfg)
    data = json.loads(cfg_path.read_text())
    assert len(data["channels"]) == 1
    assert data["channels"][0]["channel"] == "log"


def test_save_multiple_configs(notifier: Notifier):
    notifier.save(NotifyConfig(channel="log"))
    notifier.save(NotifyConfig(channel="webhook", webhook_url="http://a.com"))
    assert len(notifier._configs) == 2


def test_send_log_channel_returns_success(notifier: Notifier):
    notifier.save(NotifyConfig(channel="log"))
    results = notifier.send("push", "hello")
    assert len(results) == 1
    assert results[0].success
    assert results[0].channel == "log"


def test_send_unknown_channel_returns_error(notifier: Notifier):
    notifier.save(NotifyConfig(channel="slack"))
    results = notifier.send("push", "hello")
    assert not results[0].success
    assert "unknown channel" in results[0].error


def test_send_webhook_success(notifier: Notifier):
    notifier.save(NotifyConfig(channel="webhook", webhook_url="http://example.com/hook"))
    with patch("envoy.notify.urllib.request.urlopen") as mock_open:
        mock_open.return_value = MagicMock()
        results = notifier.send("push", "deployed")
    assert results[0].success


def test_send_webhook_failure_captured(notifier: Notifier):
    notifier.save(NotifyConfig(channel="webhook", webhook_url="http://bad.invalid"))
    with patch("envoy.notify.urllib.request.urlopen", side_effect=OSError("refused")):
        results = notifier.send("push", "deployed")
    assert not results[0].success
    assert "refused" in results[0].error


def test_notifier_loads_existing_config(cfg_path: Path):
    cfg_path.write_text(json.dumps({"channels": [{"channel": "log"}]}))
    n = Notifier(cfg_path)
    assert len(n._configs) == 1
    assert n._configs[0].channel == "log"
