"""Promote an env from one environment stage to another (e.g. staging -> production)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envoy.vault import Vault


@dataclass
class PromoteResult:
    source: str
    target: str
    keys_copied: int
    skipped_keys: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __repr__(self) -> str:  # pragma: no cover
        status = "ok" if self.success else f"error={self.error}"
        return (
            f"PromoteResult(source={self.source!r}, target={self.target!r}, "
            f"keys_copied={self.keys_copied}, skipped={len(self.skipped_keys)}, {status})"
        )


def promote_env(
    vault: Vault,
    project: str,
    source_env: str,
    target_env: str,
    password: str,
    overwrite: bool = False,
    skip_keys: Optional[List[str]] = None,
) -> PromoteResult:
    """Copy env vars from *source_env* into *target_env* for *project*.

    Parameters
    ----------
    vault:       Vault instance to read/write from.
    project:     Project name shared by both environments.
    source_env:  Name of the source environment (e.g. ``"staging"``).
    target_env:  Name of the destination environment (e.g. ``"production"``).
    password:    Encryption password used for both environments.
    overwrite:   When *False* (default) keys already present in *target_env*
                 are preserved; when *True* they are overwritten.
    skip_keys:   Optional list of key names to exclude from promotion.
    """
    skip_keys = skip_keys or []

    try:
        src_content = vault.pull(project, source_env, password)
    except Exception as exc:  # noqa: BLE001
        return PromoteResult(source=source_env, target=target_env, keys_copied=0, error=str(exc))

    # Parse source
    src_pairs: dict[str, str] = {}
    for line in src_content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        src_pairs[k.strip()] = v.strip()

    # Parse existing target (may not exist yet)
    tgt_pairs: dict[str, str] = {}
    try:
        tgt_content = vault.pull(project, target_env, password)
        for line in tgt_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            tgt_pairs[k.strip()] = v.strip()
    except Exception:  # noqa: BLE001
        pass  # target does not exist yet — that's fine

    skipped: List[str] = []
    copied = 0
    for key, value in src_pairs.items():
        if key in skip_keys:
            skipped.append(key)
            continue
        if not overwrite and key in tgt_pairs:
            skipped.append(key)
            continue
        tgt_pairs[key] = value
        copied += 1

    merged = "\n".join(f"{k}={v}" for k, v in tgt_pairs.items())
    try:
        vault.push(project, target_env, merged, password)
    except Exception as exc:  # noqa: BLE001
        return PromoteResult(source=source_env, target=target_env, keys_copied=0, error=str(exc))

    return PromoteResult(
        source=source_env,
        target=target_env,
        keys_copied=copied,
        skipped_keys=skipped,
    )
