"""Cryptographically secure password generation."""

import secrets
import string


def generate_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password."""
    if length < 4:
        length = 4
    chars = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(chars) for _ in range(length))
