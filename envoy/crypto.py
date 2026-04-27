"""Encryption and decryption utilities for .env file contents."""

import base64
import os
from typing import Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a password using Scrypt."""
    kdf = Scrypt(
        salt=salt,
        length=KEY_SIZE,
        n=2**14,
        r=8,
        p=1,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt(plaintext: Union[str, bytes], password: str) -> str:
    """Encrypt plaintext using AES-256-GCM with a password-derived key.

    Returns a base64-encoded string containing salt + nonce + ciphertext.
    """
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(encoded_payload: str, password: str) -> str:
    """Decrypt a base64-encoded payload produced by :func:`encrypt`.

    Returns the original plaintext as a UTF-8 string.
    Raises ValueError on authentication failure or malformed payload.
    """
    try:
        payload = base64.b64decode(encoded_payload)
    except Exception as exc:
        raise ValueError("Invalid base64 payload.") from exc

    min_length = SALT_SIZE + NONCE_SIZE + 16  # 16-byte GCM tag minimum
    if len(payload) < min_length:
        raise ValueError("Payload is too short to be valid.")

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed: wrong password or corrupted data.") from exc

    return plaintext.decode("utf-8")
