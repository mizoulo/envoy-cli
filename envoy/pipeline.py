"""Pipeline: chain multiple envoy operations into a single named workflow."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class PipelineStep:
    action: str          # e.g. "lint", "validate", "push", "snapshot"
    args: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"action": self.action, "args": self.args}

    @classmethod
    def from_dict(cls, d: dict) -> "PipelineStep":
        return cls(action=d["action"], args=d.get("args", {}))


@dataclass
class PipelineResult:
    name: str
    steps_run: int
    failed_step: Optional[str] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:
        status = "ok" if self.success else f"failed at '{self.failed_step}'"
        return f"<PipelineResult name={self.name!r} steps={self.steps_run} status={status}>"


class PipelineManager:
    def __init__(self, pipelines_dir: Path) -> None:
        self._dir = Path(pipelines_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self._dir / f"{name}.json"

    def save(self, name: str, steps: List[PipelineStep]) -> None:
        data = {"name": name, "steps": [s.to_dict() for s in steps]}
        self._path(name).write_text(json.dumps(data, indent=2))

    def load(self, name: str) -> List[PipelineStep]:
        p = self._path(name)
        if not p.exists():
            raise FileNotFoundError(f"Pipeline '{name}' not found.")
        data = json.loads(p.read_text())
        return [PipelineStep.from_dict(s) for s in data["steps"]]

    def list_pipelines(self) -> List[str]:
        return sorted(p.stem for p in self._dir.glob("*.json"))

    def delete(self, name: str) -> bool:
        p = self._path(name)
        if p.exists():
            p.unlink()
            return True
        return False

    def run(self, name: str, executor) -> PipelineResult:
        """Run a saved pipeline. executor(action, args) -> (ok, err_msg)."""
        try:
            steps = self.load(name)
        except FileNotFoundError as exc:
            return PipelineResult(name=name, steps_run=0, error=str(exc))

        for i, step in enumerate(steps):
            ok, err = executor(step.action, step.args)
            if not ok:
                return PipelineResult(
                    name=name,
                    steps_run=i,
                    failed_step=step.action,
                    error=err,
                )
        return PipelineResult(name=name, steps_run=len(steps))
