"""Hook system for envoy-cli lifecycle events."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


HOOK_EVENTS = (
    "pre-push",
    "post-push",
    "pre-pull",
    "post-pull",
)


@dataclass
class HookResult:
    event: str
    script: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0

    def __repr__(self) -> str:
        status = "ok" if self.success else f"exit={self.returncode}"
        return f"<HookResult event={self.event!r} {status}>"


class HookRunner:
    """Discovers and executes shell hooks for envoy lifecycle events."""

    def __init__(self, hooks_dir: Path) -> None:
        self.hooks_dir = Path(hooks_dir)

    def _hook_path(self, event: str) -> Optional[Path]:
        candidate = self.hooks_dir / event
        if candidate.exists() and candidate.is_file():
            return candidate
        return None

    def run(self, event: str, env: Optional[dict] = None) -> Optional[HookResult]:
        """Run the hook script for *event*. Returns None if no hook is defined."""
        if event not in HOOK_EVENTS:
            raise ValueError(f"Unknown hook event: {event!r}. Valid: {HOOK_EVENTS}")

        script = self._hook_path(event)
        if script is None:
            return None

        result = subprocess.run(
            [str(script)],
            capture_output=True,
            text=True,
            env=env,
        )
        return HookResult(
            event=event,
            script=str(script),
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def list_hooks(self) -> List[str]:
        """Return the names of all installed hooks."""
        if not self.hooks_dir.exists():
            return []
        return [
            p.name
            for p in sorted(self.hooks_dir.iterdir())
            if p.name in HOOK_EVENTS and p.is_file()
        ]
