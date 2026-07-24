"""Fernet-based encryption and decryption for stored passwords."""

from cryptography.fernet import Fernet, InvalidToken

_fernet: Fernet | None = None


def init_fernet(key: bytes) -> None:
    """Initialise the global Fernet cipher with the given key."""
    global _fernet
    _fernet = Fernet(key)


def encrypt_password(password: str) -> str:
    """Encrypt a plaintext password and return the token as a string."""
    return _fernet.encrypt(password.encode()).decode()


def decrypt_password(token: str) -> str:
    """Decrypt a token back to plaintext; return empty string on failure."""
    try:
        return _fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return ""
