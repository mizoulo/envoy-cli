"""Tests for envoy.pipeline."""
import pytest
from pathlib import Path
from envoy.pipeline import PipelineStep, PipelineResult, PipelineManager


@pytest.fixture
def manager(tmp_path):
    return PipelineManager(tmp_path / "pipelines")


# ---------------------------------------------------------------------------
# PipelineStep
# ---------------------------------------------------------------------------

def test_step_round_trip():
    step = PipelineStep(action="lint", args={"strict": True})
    assert PipelineStep.from_dict(step.to_dict()) == step


def test_step_default_args():
    step = PipelineStep(action="push")
    assert step.args == {}


# ---------------------------------------------------------------------------
# PipelineResult
# ---------------------------------------------------------------------------

def test_result_success_when_no_error():
    r = PipelineResult(name="deploy", steps_run=3)
    assert r.success is True


def test_result_failure_when_error():
    r = PipelineResult(name="deploy", steps_run=1, failed_step="lint", error="bad")
    assert r.success is False


def test_result_repr_contains_name_and_status():
    r = PipelineResult(name="ci", steps_run=2)
    assert "ci" in repr(r)
    assert "ok" in repr(r)


def test_result_repr_shows_failed_step():
    r = PipelineResult(name="ci", steps_run=1, failed_step="validate", error="oops")
    assert "validate" in repr(r)


# ---------------------------------------------------------------------------
# PipelineManager
# ---------------------------------------------------------------------------

def test_save_and_load_round_trip(manager):
    steps = [PipelineStep("lint"), PipelineStep("push", {"env": "prod"})]
    manager.save("deploy", steps)
    loaded = manager.load("deploy")
    assert [s.action for s in loaded] == ["lint", "push"]
    assert loaded[1].args == {"env": "prod"}


def test_load_missing_raises(manager):
    with pytest.raises(FileNotFoundError):
        manager.load("ghost")


def test_list_pipelines_empty(manager):
    assert manager.list_pipelines() == []


def test_list_pipelines_returns_names(manager):
    manager.save("alpha", [PipelineStep("lint")])
    manager.save("beta", [PipelineStep("push")])
    assert manager.list_pipelines() == ["alpha", "beta"]


def test_delete_existing(manager):
    manager.save("tmp", [PipelineStep("lint")])
    assert manager.delete("tmp") is True
    assert "tmp" not in manager.list_pipelines()


def test_delete_missing_returns_false(manager):
    assert manager.delete("ghost") is False


def test_run_all_steps_succeed(manager):
    manager.save("ci", [PipelineStep("lint"), PipelineStep("push")])

    def executor(action, args):
        return True, None

    result = manager.run("ci", executor)
    assert result.success
    assert result.steps_run == 2


def test_run_stops_on_first_failure(manager):
    manager.save("ci", [PipelineStep("lint"), PipelineStep("push")])
    calls = []

    def executor(action, args):
        calls.append(action)
        if action == "lint":
            return False, "lint failed"
        return True, None

    result = manager.run("ci", executor)
    assert not result.success
    assert result.failed_step == "lint"
    assert "push" not in calls


def test_run_missing_pipeline(manager):
    result = manager.run("ghost", lambda a, kw: (True, None))
    assert not result.success
    assert result.steps_run == 0
