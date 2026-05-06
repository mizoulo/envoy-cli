"""Namespace support: group env files under logical namespaces within a project."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envoy.vault import Vault


@dataclass
class NamespaceResult:
    action: str
    namespace: str
    success: bool
    error: Optional[str] = None

    def __bool__(self) -> bool:  # pragma: no cover
        return self.success

    def __repr__(self) -> str:
        status = "ok" if self.success else f"err={self.error}"
        return f"<NamespaceResult action={self.action} ns={self.namespace} {status}>"


class NamespaceManager:
    """Manage namespaced env files stored inside a Vault.

    A namespace is a logical prefix, e.g. "backend" or "infra/db", that
    allows multiple independent env files to coexist in the same project
    without key collisions in the underlying storage.
    """

    _META_KEY = "__namespaces__"

    def __init__(self, vault: Vault) -> None:
        self._vault = vault

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ns_env(self, namespace: str, env: str) -> str:
        """Return the composite storage key for a namespaced env."""
        return f"{namespace}/{env}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push(self, namespace: str, env: str, content: str, password: str) -> NamespaceResult:
        """Encrypt and store *content* under *namespace/env*."""
        try:
            key = self._ns_env(namespace, env)
            self._vault.push(key, content, password)
            return NamespaceResult(action="push", namespace=namespace, success=True)
        except Exception as exc:  # pragma: no cover
            return NamespaceResult(action="push", namespace=namespace, success=False, error=str(exc))

    def pull(self, namespace: str, env: str, password: str) -> str:
        """Decrypt and return the content stored under *namespace/env*."""
        key = self._ns_env(namespace, env)
        return self._vault.pull(key, password)

    def list_envs(self, namespace: str) -> List[str]:
        """Return all env names stored under *namespace*."""
        prefix = f"{namespace}/"
        all_keys = self._vault.list_envs()
        return [
            k[len(prefix):] for k in all_keys if k.startswith(prefix)
        ]

    def list_namespaces(self) -> List[str]:
        """Return all distinct namespaces present in the vault."""
        seen: List[str] = []
        for key in self._vault.list_envs():
            if "/" in key:
                ns = key.split("/", 1)[0]
                if ns not in seen:
                    seen.append(ns)
        return seen

    def delete(self, namespace: str, env: str) -> NamespaceResult:
        """Remove the env stored under *namespace/env*."""
        try:
            key = self._ns_env(namespace, env)
            self._vault.delete(key)
            return NamespaceResult(action="delete", namespace=namespace, success=True)
        except Exception as exc:
            return NamespaceResult(action="delete", namespace=namespace, success=False, error=str(exc))
