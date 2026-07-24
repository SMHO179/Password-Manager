"""Encryption key file management."""

import os
import stat

from cryptography.fernet import Fernet

from app.config import KEY_FILE


def load_or_create_key() -> bytes:
    """Load the existing key file or generate a new one."""
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    return key


def generate_key_file() -> None:
    """Generate a new encryption key and write it to disk."""
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    try:
        os.chmod(str(KEY_FILE), stat.S_IRUSR | stat.S_IWUSR)
    except PermissionError:
        pass
