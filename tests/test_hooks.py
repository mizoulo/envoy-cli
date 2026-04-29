"""Tests for envoy.hooks."""
import stat
from pathlib import Path

import pytest

from envoy.hooks import HookResult, HookRunner, HOOK_EVENTS


@pytest.fixture()
def hooks_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".envoy" / "hooks"
    d.mkdir(parents=True)
    return d


@pytest.fixture()
def runner(hooks_dir: Path) -> HookRunner:
    return HookRunner(hooks_dir)


def _make_script(path: Path, exit_code: int = 0, output: str = "") -> None:
    path.write_text(f"#!/bin/sh\necho '{output}'\nexit {exit_code}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def test_list_hooks_empty(runner: HookRunner) -> None:
    assert runner.list_hooks() == []


def test_list_hooks_returns_installed(runner: HookRunner, hooks_dir: Path) -> None:
    _make_script(hooks_dir / "pre-push")
    _make_script(hooks_dir / "post-pull")
    hooks = runner.list_hooks()
    assert "pre-push" in hooks
    assert "post-pull" in hooks


def test_run_returns_none_when_no_hook(runner: HookRunner) -> None:
    result = runner.run("pre-push")
    assert result is None


def test_run_success_hook(runner: HookRunner, hooks_dir: Path) -> None:
    _make_script(hooks_dir / "post-push", exit_code=0, output="pushed")
    result = runner.run("post-push")
    assert result is not None
    assert result.success is True
    assert result.returncode == 0
    assert "pushed" in result.stdout


def test_run_failing_hook(runner: HookRunner, hooks_dir: Path) -> None:
    _make_script(hooks_dir / "pre-pull", exit_code=1)
    result = runner.run("pre-pull")
    assert result is not None
    assert result.success is False
    assert result.returncode == 1


def test_run_unknown_event_raises(runner: HookRunner) -> None:
    with pytest.raises(ValueError, match="Unknown hook event"):
        runner.run("on-explode")


def test_hook_result_repr(runner: HookRunner, hooks_dir: Path) -> None:
    _make_script(hooks_dir / "pre-push")
    result = runner.run("pre-push")
    assert result is not None
    assert "pre-push" in repr(result)
    assert "ok" in repr(result)


def test_hook_result_repr_failure(hooks_dir: Path) -> None:
    r = HookResult(event="pre-push", script="x", returncode=2, stdout="", stderr="err")
    assert "exit=2" in repr(r)


def test_list_hooks_ignores_unknown_files(runner: HookRunner, hooks_dir: Path) -> None:
    _make_script(hooks_dir / "pre-push")
    (hooks_dir / "README").write_text("docs")
    assert "README" not in runner.list_hooks()
