"""Export .env files to various formats (shell, JSON, Docker)."""
from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from typing import Dict, Literal

ExportFormat = Literal["shell", "json", "docker"]


@dataclass
class ExportResult:
    format: ExportFormat
    content: str
    key_count: int

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ExportResult format={self.format!r} keys={self.key_count}>"


def _parse_env(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines, skipping comments and blanks."""
    pairs: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            pairs[key] = value
    return pairs


def export_env(text: str, fmt: ExportFormat = "shell") -> ExportResult:
    """Convert an env file string to the requested export format."""
    pairs = _parse_env(text)

    if fmt == "shell":
        lines = [f"export {k}={shlex.quote(v)}" for k, v in pairs.items()]
        content = "\n".join(lines)
    elif fmt == "json":
        content = json.dumps(pairs, indent=2)
    elif fmt == "docker":
        lines = [f"--env {k}={shlex.quote(v)}" for k, v in pairs.items()]
        content = " ".join(lines)
    else:
        raise ValueError(f"Unknown export format: {fmt!r}")

    return ExportResult(format=fmt, content=content, key_count=len(pairs))
