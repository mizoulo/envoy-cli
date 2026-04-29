"""Tests for envoy.rotate — key rotation of encrypted vault entries."""

import pytest

from envoy.crypto import decrypt, encrypt
from envoy.rotate import KeyRotator, RotationResult, rotate_vault_key
from envoy.vault import Vault


OLD_PASSWORD = "old-secret"
NEW_PASSWORD = "new-secret"


@pytest.fixture()
def vault(tmp_path):
    return Vault(storage_dir=tmp_path, default_password=OLD_PASSWORD)


def _push_raw(vault: Vault, name: str, plaintext: str, password: str) -> None:
    """Helper: encrypt plaintext and store directly via internal storage."""
    blob = encrypt(plaintext.encode(), password)
    vault._storage.save(name, blob)


# ---------------------------------------------------------------------------
# RotationResult
# ---------------------------------------------------------------------------

def test_rotation_result_success_when_no_failures():
    r = RotationResult(rotated=["a", "b"], failed=[])
    assert r.success is True


def test_rotation_result_failure_when_any_failed():
    r = RotationResult(rotated=["a"], failed=["b"])
    assert r.success is False


def test_rotation_result_repr_contains_counts():
    r = RotationResult(rotated=["x"], failed=["y"])
    text = repr(r)
    assert "1" in text


# ---------------------------------------------------------------------------
# KeyRotator
# ---------------------------------------------------------------------------

def test_rotate_single_env(vault):
    _push_raw(vault, "production", "KEY=value", OLD_PASSWORD)

    result = rotate_vault_key(vault, OLD_PASSWORD, NEW_PASSWORD)

    assert result.success
    assert "production" in result.rotated

    # Verify the blob is now decryptable with the new password
    blob = vault._storage.load("production")
    plaintext = decrypt(blob, NEW_PASSWORD)
    assert plaintext == b"KEY=value"


def test_rotate_multiple_envs(vault):
    for name in ("dev", "staging", "prod"):
        _push_raw(vault, name, f"{name.upper()}_VAR=1", OLD_PASSWORD)

    result = rotate_vault_key(vault, OLD_PASSWORD, NEW_PASSWORD)

    assert result.success
    assert set(result.rotated) == {"dev", "staging", "prod"}


def test_rotate_old_password_no_longer_works(vault):
    _push_raw(vault, "myenv", "SECRET=abc", OLD_PASSWORD)
    rotate_vault_key(vault, OLD_PASSWORD, NEW_PASSWORD)

    blob = vault._storage.load("myenv")
    with pytest.raises(Exception):
        decrypt(blob, OLD_PASSWORD)


def test_rotate_empty_vault_returns_empty_result(vault):
    result = rotate_vault_key(vault, OLD_PASSWORD, NEW_PASSWORD)
    assert result.rotated == []
    assert result.failed == []
    assert result.success is True
