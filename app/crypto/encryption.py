"""Fernet-based encryption and decryption for stored passwords.

Fernet provides authenticated encryption (AES-128-CBC + HMAC-SHA256) with a
fresh random IV per token, so tampering, truncation, or a wrong key is
always detected at decryption time.
"""

from cryptography.fernet import Fernet, InvalidToken

_fernet: Fernet | None = None


class EncryptionError(Exception):
    """Raised when encryption cannot proceed (e.g. not initialised)."""


class DecryptionError(EncryptionError):
    """Raised when a stored token fails authentication.

    A token can fail because it was tampered with, truncated, corrupted, or
    encrypted with a different key. It must never be mistaken for a valid
    empty password, so decryption errors are surfaced instead of swallowed.
    """


def init_fernet(key: bytes) -> None:
    """Initialise the global Fernet cipher with the given key.

    Raises EncryptionError when the key is not a valid Fernet key.
    """
    global _fernet
    try:
        _fernet = Fernet(key)
    except (ValueError, TypeError) as exc:
        raise EncryptionError("invalid encryption key") from exc


def _cipher() -> Fernet:
    if _fernet is None:
        raise EncryptionError("encryption not initialised; call init_fernet() first")
    return _fernet


def encrypt_password(password: str) -> str:
    """Encrypt a plaintext password and return the token as a string."""
    return _cipher().encrypt(password.encode()).decode()


def decrypt_password(token: str) -> str:
    """Decrypt a token back to plaintext.

    Raises DecryptionError when the token is not valid, authenticated
    ciphertext (tampered, truncated, corrupt, or from another key).
    """
    if not isinstance(token, str) or not token:
        raise DecryptionError("vault entry is missing or malformed")
    try:
        return _cipher().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError, TypeError) as exc:
        raise DecryptionError(
            "vault entry failed authentication (wrong key or tampered data)"
        ) from exc
