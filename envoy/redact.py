"""Redaction utilities for .env file values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys whose values should always be fully redacted
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth|credential)", re.I),
]

_MASK = "***"
_PARTIAL_VISIBLE = 4  # characters to reveal at end for partial masking


@dataclass
class RedactResult:
    original_count: int
    redacted_count: int
    lines: List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return f"{self.redacted_count}/{self.original_count} values redacted"

    def __repr__(self) -> str:  # pragma: no cover
        return f"RedactResult({self.summary})"

    def to_string(self) -> str:
        """Return the redacted lines joined as a single string."""
        return "\n".join(self.lines)


def _is_sensitive(key: str) -> bool:
    """Return True if the key name matches any sensitive pattern."""
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def _mask_value(value: str, partial: bool = False) -> str:
    """Mask a value fully or partially."""
    if not value:
        return value
    if partial and len(value) > _PARTIAL_VISIBLE:
        return _MASK + value[-_PARTIAL_VISIBLE:]
    return _MASK


def redact_env(
    content: str,
    extra_keys: Optional[List[str]] = None,
    partial: bool = False,
) -> RedactResult:
    """Redact sensitive values in a .env file string.

    Args:
        content:    Raw .env file text.
        extra_keys: Additional key names to treat as sensitive.
        partial:    If True, reveal the last few characters of each value.

    Returns:
        RedactResult with redacted lines and counts.
    """
    sensitive_extra: List[re.Pattern] = []
    for key in (extra_keys or []):
        sensitive_extra.append(re.compile(re.escape(key), re.I))

    output_lines: List[str] = []
    original_count = 0
    redacted_count = 0

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            output_lines.append(line)
            continue

        if "=" not in stripped:
            output_lines.append(line)
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        original_count += 1

        is_extra = any(p.search(key) for p in sensitive_extra)
        if _is_sensitive(key) or is_extra:
            masked = _mask_value(value, partial=partial)
            output_lines.append(f"{key}={masked}")
            redacted_count += 1
        else:
            output_lines.append(line)

    return RedactResult(
        original_count=original_count,
        redacted_count=redacted_count,
        lines=output_lines,
    )
