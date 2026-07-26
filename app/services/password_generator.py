"""Cryptographically secure password generation."""

import secrets
import string

_CHARS = string.ascii_letters + string.digits + string.punctuation


def generate_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password."""
    if length < 4:
        length = 4
    return "".join(secrets.choice(_CHARS) for _ in range(length))
