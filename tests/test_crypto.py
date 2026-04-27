"""Tests for envoy.crypto encryption/decryption utilities."""

import pytest

from envoy.crypto import decrypt, encrypt


PASSWORD = "super-secret-passphrase"
SAMPLE_ENV = "DATABASE_URL=postgres://user:pass@localhost/db\nDEBUG=true\n"


def test_encrypt_returns_string():
    result = encrypt(SAMPLE_ENV, PASSWORD)
    assert isinstance(result, str)
    assert len(result) > 0


def test_encrypt_produces_unique_ciphertexts():
    """Each encryption call should produce a different ciphertext (random salt/nonce)."""
    result1 = encrypt(SAMPLE_ENV, PASSWORD)
    result2 = encrypt(SAMPLE_ENV, PASSWORD)
    assert result1 != result2


def test_round_trip_string():
    ciphertext = encrypt(SAMPLE_ENV, PASSWORD)
    recovered = decrypt(ciphertext, PASSWORD)
    assert recovered == SAMPLE_ENV


def test_round_trip_bytes_input():
    plaintext_bytes = SAMPLE_ENV.encode("utf-8")
    ciphertext = encrypt(plaintext_bytes, PASSWORD)
    recovered = decrypt(ciphertext, PASSWORD)
    assert recovered == SAMPLE_ENV


def test_decrypt_wrong_password_raises():
    ciphertext = encrypt(SAMPLE_ENV, PASSWORD)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(ciphertext, "wrong-password")


def test_decrypt_tampered_payload_raises():
    ciphertext = encrypt(SAMPLE_ENV, PASSWORD)
    # Flip a byte near the end of the base64 payload
    tampered = ciphertext[:-4] + "AAAA"
    with pytest.raises(ValueError):
        decrypt(tampered, PASSWORD)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid base64"):
        decrypt("not-valid-base64!!!", PASSWORD)


def test_decrypt_too_short_payload_raises():
    import base64
    short_payload = base64.b64encode(b"tooshort").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short_payload, PASSWORD)


def test_empty_string_round_trip():
    ciphertext = encrypt("", PASSWORD)
    recovered = decrypt(ciphertext, PASSWORD)
    assert recovered == ""
