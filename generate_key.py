"""Standalone entry point for generating a new encryption key."""

import sys

from app.config import KEY_FILE
from app.crypto.key_manager import generate_key_file

if KEY_FILE.exists():
    print("Warning: Key already exists!")
    print("Generating a new key will destroy access to existing passwords.")
    sys.exit(1)

generate_key_file()
print(f"Encryption key created successfully at {KEY_FILE.absolute()}")
