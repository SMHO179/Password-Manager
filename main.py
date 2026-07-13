"""Password Manager — a CLI tool for securely storing and managing credentials."""

import os
import random
import sqlite3
import stat
import string
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

# ── Constants ────────────────────────────────────────────────────────────────

VERSION = "1.3.0"
DB_NAME = Path("vault.db")
KEY_FILE = Path("secret.key")

STYLE = {
    "primary": "cyan",
    "success": "green",
    "warn": "yellow",
    "error": "red",
    "muted": "bright_black",
    "accent": "magenta",
    "header": "bold cyan",
    "border": "cyan",
}

console = Console()

# ── SQL Queries ──────────────────────────────────────────────────────────────

SQL_CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS passwords(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SQL_INSERT_PASSWORD = """\
INSERT INTO passwords(site, username, password)
VALUES (?, ?, ?)
"""

SQL_SELECT_PASSWORDS = """\
SELECT id, site, username, created_at
FROM passwords
ORDER BY id DESC
"""

SQL_DELETE_PASSWORD = "DELETE FROM passwords WHERE id = ?"

SQL_UPDATE_PASSWORD = """\
UPDATE passwords
SET site = ?, username = ?, password = ?
WHERE id = ?
"""

# ── Encryption key (initialised lazily in __main__) ──────────────────────────

fernet: Fernet  # assigned in the __main__ block; always available before use


# ── Utilities ────────────────────────────────────────────────────────────────


def check_password_strength(password: str) -> tuple[str, str]:
    """Return a (label, colour) pair describing password strength."""
    score = 0
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1

    if score <= 2:
        return "Weak", "red"
    if score <= 4:
        return "Medium", "yellow"
    if score == 5:
        return "Strong", "green"
    return "Very Strong", "bright_green"


def make_section_panel(title: str) -> Panel:
    """Create a section heading panel with the standard border style."""
    return Panel(f"[bold]{title}[/bold]", border_style=STYLE["border"])


def prompt_or_back(text: str, *, password: bool = False) -> str | None:
    """Prompt for input; return None when the user types 'b' to go back."""
    value = Prompt.ask(text, password=password)
    return None if value.lower() == "b" else value


def pause() -> None:
    """Wait for Enter before returning to the menu."""
    Prompt.ask("\nPress Enter to return to menu", default="")


# ── Database ─────────────────────────────────────────────────────────────────


@contextmanager
def db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for a SQLite connection with auto-commit/rollback."""
    conn = sqlite3.connect(str(DB_NAME))
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create the passwords table if it does not exist."""
    with db() as conn:
        conn.execute(SQL_CREATE_TABLE)


# ── Encryption ───────────────────────────────────────────────────────────────


def load_or_create_key() -> bytes:
    """Load the existing key file or generate a new one."""
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    console.print("[green]✔ Encryption key generated[/green]")
    return key


def encrypt_password(password: str) -> str:
    """Encrypt a plaintext password and return the token as a string."""
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(password: str) -> str:
    """Decrypt a token back to plaintext; return empty string on failure."""
    try:
        return fernet.decrypt(password.encode()).decode()
    except InvalidToken:
        return ""


# ── CRUD ─────────────────────────────────────────────────────────────────────


def add_password() -> None:
    """Prompt for a new credential and store it encrypted."""
    console.print(make_section_panel("New Credential"))

    site = prompt_or_back("Site")
    if site is None:
        return

    username = prompt_or_back("Username")
    if username is None:
        return

    password = prompt_or_back("Password", password=True)
    # NOTE: None-check intentionally placed after strength call to match
    # original order exactly (strength will crash if password is None).

    strength, color = check_password_strength(password)
    console.print(f"Password strength: [{color}]{strength}[/{color}]")
    if password is None:
        return

    encrypted = encrypt_password(password)

    with db() as conn:
        conn.execute(SQL_INSERT_PASSWORD, (site, username, encrypted))

    console.print("[green]✔ Saved securely[/green]")
    pause()


def list_passwords() -> None:
    """Display all stored credentials in a table."""
    with db() as conn:
        rows = conn.execute(SQL_SELECT_PASSWORDS).fetchall()

    if not rows:
        console.print("[yellow]No passwords found[/yellow]")
        pause()
        return

    table = Table(
        title="Password Vault",
        box=box.SIMPLE,
        border_style=STYLE["border"],
    )
    table.add_column("ID")
    table.add_column("Site")
    table.add_column("Username")
    table.add_column("Created")

    for row in rows:
        table.add_row(str(row[0]), row[1], row[2], row[3])

    console.print(table)
    pause()


def delete_password() -> None:
    """List passwords and remove the one chosen by ID."""
    list_passwords()

    entry_id = prompt_or_back("ID to delete")
    if entry_id is None:
        return

    with db() as conn:
        result = conn.execute(SQL_DELETE_PASSWORD, (entry_id,))

    if result.rowcount:
        console.print("[red]✔ Deleted[/red]")
    else:
        console.print("[yellow]ID not found[/yellow]")

    pause()


def edit_password() -> None:
    """List passwords and update the one chosen by ID with new values."""
    list_passwords()

    entry_id = prompt_or_back("ID to edit")
    if entry_id is None:
        return

    new_site = prompt_or_back("New site")
    if new_site is None:
        return

    new_username = prompt_or_back("New username")
    if new_username is None:
        return

    new_password = prompt_or_back("New password", password=True)
    if new_password is None:
        return

    encrypted = encrypt_password(new_password)

    with db() as conn:
        result = conn.execute(
            SQL_UPDATE_PASSWORD, (new_site, new_username, encrypted, entry_id)
        )

    if result.rowcount:
        console.print("[yellow]✔ Updated[/yellow]")
    else:
        console.print("[red]ID not found[/red]")

    pause()


# ── Password Generator ───────────────────────────────────────────────────────


def generate_password() -> None:
    """Generate a random password with a user-chosen length."""
    console.print(make_section_panel("Password Generator"))

    length = Prompt.ask("Length", default="16")
    try:
        length = int(length)
    except ValueError:
        length = 16

    if length < 4:
        length = 4

    chars = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(chars) for _ in range(length))

    console.print(f"\nGenerated password:\n[bold cyan]{password}[/bold cyan]")

    copy = Prompt.ask("Copy to clipboard?", choices=["y", "n"], default="y")
    if copy.lower() == "y":
        try:
            import pyperclip

            pyperclip.copy(password)
            console.print("[green]✔ Copied to clipboard[/green]")
        except ImportError:
            console.print(
                "[yellow]pyperclip not installed. "
                "Select and copy manually.[/yellow]"
            )

    pause()


# ── Key Management ───────────────────────────────────────────────────────────


def generate_key() -> None:
    """Generate a new encryption key (destructive — existing data
    will become inaccessible)."""
    if KEY_FILE.exists():
        console.print(
            Panel(
                "Key already exists!\n"
                "Generating a new key will destroy "
                "access to existing passwords.",
                title="Warning",
                border_style="red",
            )
        )
        return

    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)

    try:
        os.chmod(KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except PermissionError:
        pass

    console.print(
        Panel(
            "Encryption key created successfully\n"
            f"Location: {KEY_FILE.absolute()}",
            title="Success",
            border_style="green",
        )
    )


# ── UI ───────────────────────────────────────────────────────────────────────


def menu() -> None:
    """Display the main menu and dispatch user choices in a loop."""
    while True:
        console.print(
            Panel(
                Align.center(Text("PASSWORD MANAGER", style=STYLE["header"])),
                subtitle=f"v{VERSION}",
                border_style=STYLE["border"],
            )
        )

        console.print("""
[green]1[/] Add password
[green]2[/] List passwords
[green]3[/] Delete password
[green]4[/] Edit password
[green]5[/] Generate password
[green]6[/] Exit

[dim]Type b anytime to return[/dim]
        """)

        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "6"])

        match choice:
            case "1":
                add_password()
            case "2":
                list_passwords()
            case "3":
                delete_password()
            case "4":
                edit_password()
            case "5":
                generate_password()
            case "6":
                console.print("[cyan]Goodbye[/cyan]")
                break


def print_version() -> None:
    """Print the application version."""
    console.print(f"Password Manager v{VERSION}")


# ── Main ─────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    if "--version" in sys.argv:
        print_version()
        sys.exit()

    fernet = Fernet(load_or_create_key())

    try:
        init_db()
        menu()
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye[/dim]")
