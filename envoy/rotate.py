"""Key rotation support for re-encrypting stored .env files with a new password."""

from dataclasses import dataclass, field
from typing import List

from envoy.crypto import decrypt, encrypt
from envoy.vault import Vault


@dataclass
class RotationResult:
    rotated: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.failed) == 0

    def __repr__(self) -> str:
        return (
            f"RotationResult(rotated={len(self.rotated)}, "
            f"failed={len(self.failed)}, success={self.success})"
        )


class KeyRotator:
    """Re-encrypts all env blobs in a Vault under a new password."""

    def __init__(self, vault: Vault, old_password: str, new_password: str) -> None:
        self._vault = vault
        self._old_password = old_password
        self._new_password = new_password

    def rotate(self) -> RotationResult:
        """Iterate every stored env, decrypt with old password, re-encrypt with new."""
        result = RotationResult()
        env_names = self._vault.list_envs()

        for name in env_names:
            try:
                ciphertext = self._vault.pull(name, self._old_password)
                # pull already returns plaintext; we need raw ciphertext — use storage
                raw_blob = self._vault._storage.load(name)
                plaintext = decrypt(raw_blob, self._old_password)
                new_blob = encrypt(plaintext, self._new_password)
                self._vault._storage.save(name, new_blob)
                result.rotated.append(name)
            except Exception as exc:  # noqa: BLE001
                result.failed.append(name)
        return result


def rotate_vault_key(
    vault: Vault,
    old_password: str,
    new_password: str,
) -> RotationResult:
    """Convenience wrapper around KeyRotator."""
    rotator = KeyRotator(vault, old_password, new_password)
    return rotator.rotate()
