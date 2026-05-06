"""Import .env files from various formats into the vault."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ImportResult:
    source: str
    fmt: str
    imported: int
    skipped: int
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:
        return (
            f"ImportResult(source={self.source!r}, fmt={self.fmt!r}, "
            f"imported={self.imported}, skipped={self.skipped}, "
            f"success={self.success})"
        )


def _parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a standard .env file into a key/value dict."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def _parse_json(text: str) -> Dict[str, str]:
    """Parse a flat JSON object into a key/value dict."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return {str(k): str(v) for k, v in data.items()}


def _parse_shell(text: str) -> Dict[str, str]:
    """Parse 'export KEY=VALUE' shell export lines."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("export "):
            stripped = stripped[len("export "):].strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


_PARSERS = {
    "dotenv": _parse_dotenv,
    "json": _parse_json,
    "shell": _parse_shell,
}


def import_env(
    source_path: str,
    fmt: str = "dotenv",
    skip_existing: bool = False,
    existing_keys: Optional[List[str]] = None,
) -> tuple[Dict[str, str], ImportResult]:
    """Read and parse an env file, returning parsed pairs and a result summary."""
    if fmt not in _PARSERS:
        raise ValueError(f"Unknown format {fmt!r}. Choose from: {list(_PARSERS)}")

    text = Path(source_path).read_text(encoding="utf-8")
    parsed = _PARSERS[fmt](text)

    skipped = 0
    final: Dict[str, str] = {}
    for k, v in parsed.items():
        if skip_existing and existing_keys and k in existing_keys:
            skipped += 1
        else:
            final[k] = v

    result = ImportResult(
        source=source_path,
        fmt=fmt,
        imported=len(final),
        skipped=skipped,
    )
    return final, result
