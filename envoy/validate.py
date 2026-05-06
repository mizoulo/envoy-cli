"""Validation module for .env files against a schema/template."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __repr__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def summary(self) -> str:
        if not self.issues:
            return "All required keys present and valid."
        lines = [repr(i) for i in self.issues]
        status = "PASSED" if self.valid else "FAILED"
        lines.append(f"Validation {status}: {len(self.issues)} issue(s) found.")
        return "\n".join(lines)


def _parse_env(text: str) -> dict:
    result = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            result[key.strip()] = value.strip()
    return result


def validate_env(
    env_text: str,
    schema_text: str,
    allow_extra: bool = True,
) -> ValidationResult:
    """Validate *env_text* against *schema_text*.

    The schema is itself a .env file where:
    - A key with any value marks the key as **required**.
    - A key whose value starts with ``?`` marks it as **optional** (warning only).
    """
    env = _parse_env(env_text)
    schema = _parse_env(schema_text)
    issues: List[ValidationIssue] = []

    for key, spec in schema.items():
        optional = spec.startswith("?")
        if key not in env:
            if optional:
                issues.append(ValidationIssue(key, "Optional key missing.", "warning"))
            else:
                issues.append(ValidationIssue(key, "Required key missing.", "error"))
        elif not env[key]:
            severity = "warning" if optional else "error"
            issues.append(ValidationIssue(key, "Key present but value is empty.", severity))

    if not allow_extra:
        for key in env:
            if key not in schema:
                issues.append(ValidationIssue(key, "Undeclared key not in schema.", "warning"))

    return ValidationResult(issues=issues)
