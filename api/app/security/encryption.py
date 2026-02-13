"""AES-256-GCM encryption for PII fields (phone numbers, etc.).

Usage:
    from app.security.encryption import encrypt_field, decrypt_field

    encrypted = encrypt_field("(555) 123-4567")
    plaintext = decrypt_field(encrypted)

The encryption key is loaded from ENCRYPTION_KEY env var (base64-encoded
32 bytes). If not configured, functions are no-ops (pass-through) for
development convenience.
"""

import base64
import hashlib
import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

_KEY_BYTES: bytes | None = None


@lru_cache(maxsize=1)
def _get_key() -> bytes | None:
    """Load and validate the encryption key."""
    from app.config import settings

    if not settings.encryption_key:
        return None

    try:
        key = base64.b64decode(settings.encryption_key)
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes, got {len(key)}")
        return key
    except Exception as e:
        logger.error("Invalid ENCRYPTION_KEY: %s", e)
        return None


def encrypt_field(plaintext: str) -> str:
    """Encrypt a plaintext string using AES-256-GCM.

    Returns base64-encoded ciphertext (nonce + ciphertext + tag).
    If no key is configured, returns the plaintext unchanged.
    """
    key = _get_key()
    if key is None:
        return plaintext

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = os.urandom(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    # Prepend nonce to ciphertext for storage
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_field(encrypted: str) -> str:
    """Decrypt an AES-256-GCM encrypted string.

    If no key is configured, returns the input unchanged.
    """
    key = _get_key()
    if key is None:
        return encrypted

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    try:
        raw = base64.b64decode(encrypted)
        nonce = raw[:12]
        ciphertext = raw[12:]
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as e:
        logger.error("Decryption failed: %s", e)
        return encrypted  # Return as-is if decryption fails (legacy data)


def hash_for_lookup(value: str) -> str:
    """Generate a SHA-256 hash of a value for indexed lookups.

    This allows searching for participants by phone number hash
    without needing to decrypt every row.
    """
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


def generate_encryption_key() -> str:
    """Generate a new random encryption key (base64-encoded 32 bytes).

    Use this to generate the ENCRYPTION_KEY env var value:
        python -c "from app.security.encryption import generate_encryption_key; print(generate_encryption_key())"
    """
    return base64.b64encode(os.urandom(32)).decode("ascii")
