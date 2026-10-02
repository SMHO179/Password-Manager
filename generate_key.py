"""Standalone entry point for generating a new encryption key."""

import sys

from app.config import KEY_FILE
from app.crypto.key_manager import KeyFileError, generate_key_file

if KEY_FILE.exists():
    print("Warning: Key already exists!")
    print("Generating a new key will destroy access to existing passwords.")
    sys.exit(1)

try:
    generate_key_file()
except KeyFileError as exc:
    print(f"Error: {exc}")
    sys.exit(1)
print(f"Encryption key created successfully at {KEY_FILE.absolute()}")
