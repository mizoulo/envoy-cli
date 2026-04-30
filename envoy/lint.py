"""Lint .env files for common issues and style violations."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


_KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_VALID_LINE_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*\s*=')


@dataclass
class LintIssue:
    line_no: int
    code: str
    message: str

    def __repr__(self) -> str:
        return f"L{self.line_no} [{self.code}] {self.message}"


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.clean:
            return f"{self.path}: OK"
        lines = [f"{self.path}: {len(self.issues)} issue(s)"]
        for issue in self.issues:
            lines.append(f"  {issue!r}")
        return "\n".join(lines)


def lint_env(source: str, path: str = "<string>") -> LintResult:
    """Lint env file content and return a LintResult."""
    result = LintResult(path=path)
    seen_keys: dict[str, int] = {}

    for line_no, raw in enumerate(source.splitlines(), start=1):
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        if not _VALID_LINE_RE.match(line):
            result.issues.append(LintIssue(line_no, "E001", f"Invalid line format: {line!r}"))
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        if not _KEY_RE.match(key):
            result.issues.append(LintIssue(line_no, "W001", f"Key {key!r} is not UPPER_SNAKE_CASE"))

        if key in seen_keys:
            result.issues.append(
                LintIssue(line_no, "E002", f"Duplicate key {key!r} (first seen on L{seen_keys[key]})")
            )
        else:
            seen_keys[key] = line_no

        if value.startswith((" ", "\t")):
            result.issues.append(LintIssue(line_no, "W002", f"Value for {key!r} has leading whitespace"))

    return result


def lint_file(path: str | Path) -> LintResult:
    """Read a .env file from disk and lint it."""
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    return lint_env(content, path=str(p))
