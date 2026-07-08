import sys
import sqlite3
from pathlib import Path
from contextlib import contextmanager

from cryptography.fernet import Fernet, InvalidToken

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.align import Align
from rich.style import Style


console = Console()

DB_NAME = Path("vault.db")
KEY_FILE = Path("secret.key")

VERSION = "1.0.0"

C = {
    "primary": "cyan",
    "success": "green",
    "warn": "yellow",
    "error": "red",
    "muted": "bright_black",
    "accent": "magenta",
    "header": "bold cyan",
    "border": "cyan",
}


def load_or_create_key():
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()

    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    console.print(f"[{C['success']}]✔ Encryption key generated[/]")
    return key


fernet = Fernet(load_or_create_key())


@contextmanager
def db():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS passwords(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)


def encrypt_password(password):
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(password):
    try:
        return fernet.decrypt(password.encode()).decode()
    except InvalidToken:
        return ""


def add_password():
    console.print(Panel(
        "[bold]New Credential[/bold]",
        border_style=C["border"]
    ))

    site = Prompt.ask("Site")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)

    encrypted = encrypt_password(password)

    with db() as conn:
        conn.execute(
            "INSERT INTO passwords(site, username, password) VALUES (?, ?, ?)",
            (site, username, encrypted)
        )

    console.print("[green]✔ Saved securely[/green]")


def list_passwords():
    with db() as conn:
        rows = conn.execute(
            "SELECT id, site, username, created_at FROM passwords ORDER BY id DESC"
        ).fetchall()

    if not rows:
        console.print("[yellow]No passwords found[/yellow]")
        return

    table = Table(
        title="Password Vault",
        box=box.SIMPLE,
        border_style=C["border"]
    )

    table.add_column("ID")
    table.add_column("Site")
    table.add_column("Username")
    table.add_column("Created")

    for row in rows:
        table.add_row(
            str(row[0]),
            row[1],
            row[2],
            row[3]
        )

    console.print(table)


def delete_password():
    list_passwords()

    entry_id = Prompt.ask("ID to delete")

    with db() as conn:
        result = conn.execute(
            "DELETE FROM passwords WHERE id=?",
            (entry_id,)
        )

    console.print("[red]✔ Deleted[/red]")


def edit_password():
    list_passwords()

    entry_id = Prompt.ask("ID to edit")

    new_site = Prompt.ask("New site")
    new_username = Prompt.ask("New username")
    new_password = Prompt.ask("New password", password=True)

    encrypted = encrypt_password(new_password)

    with db() as conn:
        conn.execute(
            """
            UPDATE passwords
            SET site=?, username=?, password=?
            WHERE id=?
            """,
            (
                new_site,
                new_username,
                encrypted,
                entry_id
            )
        )

    console.print("[yellow]✔ Updated[/yellow]")


def menu():
    while True:
        console.print(
            Panel(
                Align.center(
                    Text("PASSWORD MANAGER", style=C["header"])
                ),
                subtitle=f"v{VERSION}",
                border_style=C["border"]
            )
        )

        console.print("""
[green]1[/] Add password
[green]2[/] List passwords
[green]3[/] Delete password
[green]4[/] Edit password
[green]5[/] Exit
        """)

        choice = Prompt.ask(
            "Select",
            choices=["1", "2", "3", "4", "5"]
        )

        if choice == "1":
            add_password()

        elif choice == "2":
            list_passwords()

        elif choice == "3":
            delete_password()

        elif choice == "4":
            edit_password()

        elif choice == "5":
            console.print("[cyan]Goodbye[/]")
            break


def print_version():
    console.print(f"Password Manager v{VERSION}")


if __name__ == "__main__":

    if "--version" in sys.argv:
        print_version()
        sys.exit()

    try:
        init_db()
        menu()

    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye[/]")