"""Compare .env files across environments or projects."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


def _parse_env(text: str) -> Dict[str, str]:
    """Parse env file text into a key-value dict."""
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


@dataclass
class CompareResult:
    env_a: str
    env_b: str
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    differing_values: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, val_a, val_b)
    common_keys: List[str] = field(default_factory=list)

    @property
    def is_identical(self) -> bool:
        return not self.only_in_a and not self.only_in_b and not self.differing_values

    def summary(self) -> str:
        lines = [f"Comparing '{self.env_a}' vs '{self.env_b}'"]
        if self.is_identical:
            lines.append("  ✓ Environments are identical.")
            return "\n".join(lines)
        if self.only_in_a:
            lines.append(f"  Only in {self.env_a}: {', '.join(sorted(self.only_in_a))}")
        if self.only_in_b:
            lines.append(f"  Only in {self.env_b}: {', '.join(sorted(self.only_in_b))}")
        for key, va, vb in sorted(self.differing_values):
            lines.append(f"  ~ {key}: '{va}' → '{vb}'")
        return "\n".join(lines)


def compare_envs(
    text_a: str,
    text_b: str,
    label_a: str = "a",
    label_b: str = "b",
    mask_values: bool = True,
) -> CompareResult:
    """Compare two env file strings and return a CompareResult."""
    map_a = _parse_env(text_a)
    map_b = _parse_env(text_b)
    keys_a = set(map_a)
    keys_b = set(map_b)

    only_in_a = list(keys_a - keys_b)
    only_in_b = list(keys_b - keys_a)
    common = keys_a & keys_b

    differing = []
    for key in common:
        if map_a[key] != map_b[key]:
            va = "***" if mask_values else map_a[key]
            vb = "***" if mask_values else map_b[key]
            differing.append((key, va, vb))

    return CompareResult(
        env_a=label_a,
        env_b=label_b,
        only_in_a=only_in_a,
        only_in_b=only_in_b,
        differing_values=differing,
        common_keys=list(common),
    )
