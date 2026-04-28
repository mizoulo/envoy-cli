"""High-level Vault: ties together crypto and storage."""

from pathlib import Path
from typing import Optional

from envoy.crypto import decrypt, encrypt
from envoy.storage import LocalStorage


class Vault:
    """Encrypt/decrypt .env content and persist it via LocalStorage."""

    def __init__(self, password: str, store_dir: Optional[Path] = None):
        if not password:
            raise ValueError("Password must not be empty")
        self._password = password
        self._storage = LocalStorage(store_dir)

    def push(self, project: str, env_name: str, plaintext: str) -> Path:
        """Encrypt *plaintext* and save it; returns storage path."""
        if not plaintext:
            raise ValueError("Plaintext env content must not be empty")
        ciphertext = encrypt(plaintext, self._password)
        return self._storage.save(project, env_name, ciphertext)

    def pull(self, project: str, env_name: str) -> str:
        """Load and decrypt a stored env; returns plaintext."""
        ciphertext = self._storage.load(project, env_name)
        return decrypt(ciphertext, self._password)

    def list_envs(self, project: str) -> list[str]:
        """Delegate listing to storage backend."""
        return self._storage.list_envs(project)

    def delete(self, project: str, env_name: str) -> None:
        """Remove a stored env from the vault."""
        self._storage.delete(project, env_name)

    def rotate_password(self, new_password: str, project: str, env_name: str) -> None:
        """Re-encrypt an env entry with a new password."""
        if not new_password:
            raise ValueError("New password must not be empty")
        plaintext = self.pull(project, env_name)
        self._password = new_password
        self.push(project, env_name, plaintext)
