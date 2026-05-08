"""Masking module: selectively reveal or hide env variable values for safe display."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_SENSITIVE_PATTERNS = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|auth|credential|private[_-]?key)",
    re.IGNORECASE,
)

DEFAULT_MASK = "***"
DEFAULT_REVEAL_CHARS = 4


@dataclass
class MaskResult:
    key: str
    original: str
    masked: str
    sensitive: bool

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MaskResult key={self.key!r} sensitive={self.sensitive}>"


@dataclass
class MaskReport:
    results: List[MaskResult] = field(default_factory=list)

    @property
    def sensitive_count(self) -> int:
        return sum(1 for r in self.results if r.sensitive)

    @property
    def plain_count(self) -> int:
        return sum(1 for r in self.results if not r.sensitive)

    def as_dict(self) -> Dict[str, str]:
        return {r.key: r.masked for r in self.results}

    def summary(self) -> str:
        return (
            f"{len(self.results)} keys ({self.sensitive_count} masked, "
            f"{self.plain_count} visible)"
        )


def _is_sensitive(key: str) -> bool:
    return bool(_SENSITIVE_PATTERNS.search(key))


def _mask_value(
    value: str,
    reveal_chars: int = DEFAULT_REVEAL_CHARS,
    mask: str = DEFAULT_MASK,
) -> str:
    if not value:
        return mask
    if len(value) <= reveal_chars:
        return mask
    return value[:reveal_chars] + mask


def mask_env(
    env: Dict[str, str],
    reveal_chars: int = DEFAULT_REVEAL_CHARS,
    mask: str = DEFAULT_MASK,
    force_mask: Optional[List[str]] = None,
    force_reveal: Optional[List[str]] = None,
) -> MaskReport:
    """Produce a MaskReport for the given env dict."""
    force_mask_set = set(force_mask or [])
    force_reveal_set = set(force_reveal or [])
    results: List[MaskResult] = []
    for key, value in env.items():
        if key in force_reveal_set:
            sensitive = False
        elif key in force_mask_set or _is_sensitive(key):
            sensitive = True
        else:
            sensitive = False
        masked = _mask_value(value, reveal_chars, mask) if sensitive else value
        results.append(MaskResult(key=key, original=value, masked=masked, sensitive=sensitive))
    return MaskReport(results=results)
