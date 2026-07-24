"""Password Manager — a CLI tool for securely storing and managing credentials."""

import sys

from app.cli import console
from app.cli.menu import menu, print_version
from app.config import KEY_FILE
from app.crypto.encryption import init_fernet
from app.crypto.key_manager import load_or_create_key
from app.database.connection import init_db
from app.database.repository import Repository
from app.services.password_service import PasswordService

if __name__ == "__main__":
    if "--version" in sys.argv:
        print_version()
        sys.exit()

    key_was_created = not KEY_FILE.exists()
    key = load_or_create_key()
    if key_was_created:
        console.print("[green]✔ Encryption key generated[/green]")

    init_fernet(key)

    try:
        init_db()
        service = PasswordService(Repository())
        menu(service)
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye[/dim]")
