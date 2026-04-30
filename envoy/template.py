"""Template rendering for .env files — substitute variables and generate env from templates."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_VAR_RE = re.compile(r"\{\{\s*([A-Z_][A-Z0-9_]*)\s*\}\}")


@dataclass
class RenderResult:
    output: str
    missing: List[str] = field(default_factory=list)
    substituted: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.missing) == 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RenderResult(success={self.success}, "
            f"substituted={self.substituted}, missing={self.missing})"
        )


def render_template(template: str, variables: Dict[str, str]) -> RenderResult:
    """Replace {{VAR}} placeholders with values from *variables*."""
    missing: List[str] = []
    substituted: List[str] = []

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key in variables:
            substituted.append(key)
            return variables[key]
        missing.append(key)
        return match.group(0)

    output = _VAR_RE.sub(_replace, template)
    return RenderResult(output=output, missing=list(dict.fromkeys(missing)), substituted=list(dict.fromkeys(substituted)))


def render_template_file(
    template_path: Path,
    variables: Dict[str, str],
    output_path: Optional[Path] = None,
) -> RenderResult:
    """Read a template file, render it, and optionally write the result."""
    template = template_path.read_text(encoding="utf-8")
    result = render_template(template, variables)
    if output_path is not None:
        output_path.write_text(result.output, encoding="utf-8")
    return result


def collect_placeholders(template: str) -> List[str]:
    """Return a deduplicated list of placeholder names found in *template*."""
    seen: Dict[str, None] = {}
    for match in _VAR_RE.finditer(template):
        seen[match.group(1)] = None
    return list(seen)
