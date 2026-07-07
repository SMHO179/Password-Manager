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
    console.print(f" [{C['success']}]✔[/] Encryption key generated")
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
    console.print()
    console.print(Panel(
        "[bold]New Credential[/bold]",
        subtitle="fill in the fields below",
        subtitle_align="right",
        border_style=C["border"],
        padding=(1, 2),
    ))
    console.print(f" [{C['muted']}]type [b]b[/b] at any prompt to cancel[/]")

    site = Prompt.ask(f" [{C['warn']}]●[/] Site")
    if not site.strip() or site.strip().lower() == "b":
        return

    username = Prompt.ask(f" [{C['warn']}]●[/] Username")
    if not username.strip() or username.strip().lower() == "b":
        return

    password = Prompt.ask(f" [{C['warn']}]●[/] Password", password=True)
    if not password.strip() or password.strip().lower() == "b":
        return

    encrypted = encrypt_password(password)

    with db() as conn:
        conn.execute(
            "INSERT INTO passwords (site, username, password) VALUES (?, ?, ?)",
            (site.strip(), username.strip(), encrypted),
        )

    console.print(f" [{C['success']}]✔[/] [bold]Saved securely[/bold]")


def list_passwords():
    with db() as conn:
        cur = conn.execute(
            "SELECT id, site, username, password, created_at FROM passwords ORDER BY created_at DESC"
        )
        rows = cur.fetchall()

    if not rows:
        console.print()
        console.print(Panel(
            Align.center("[dim]No credentials yet[/dim]"),
            border_style=C["warn"],
            padding=(1, 2),
        ))
    else:
        table = Table(
            title="Password Vault",
            title_style=C["header"],
            caption=f"{len(rows)} credential{'s' if len(rows) != 1 else ''} stored",
            caption_style=C["muted"],
            box=box.SIMPLE,
            border_style=C["muted"],
            header_style=Style(bold=True, color=C["primary"]),
            padding=(0, 1),
        )

        table.add_column("ID", style=C["muted"], width=4)
        table.add_column("Site", style=C["success"], no_wrap=True)
        table.add_column("Username", style=C["warn"], no_wrap=True)
        table.add_column("Password", style=C["muted"])
        table.add_column("Created", style=C["accent"], no_wrap=True)

        for row in rows:
            table.add_row(str(row[0]), row[1], row[2], "••••••••", row[4])

        console.print()
        console.print(table)

    Prompt.ask(f" [{C['muted']}]press Enter to go back[/]")


def menu():
    while True:
        console.print()
        console.print(Panel(
            Align.center(Text(
                "PASSWORD MANAGER",
                style=C["header"],
            )),
            subtitle=f"v{VERSION}",
            subtitle_align="right",
            border_style=C["border"],
            padding=(1, 2),
        ))

        for key, label in [("1", "Add password"), ("2", "List passwords"), ("3", "Exit")]:
            console.print(f"  [{C['success']}]{key}[/]    {label}")

        console.print()
        choice = Prompt.ask(f" [{C['primary']}]→[/] Select", choices=["1", "2", "3"])

        match choice:
            case "1":
                add_password()
            case "2":
                list_passwords()
            case "3":
                console.print()
                console.print(Panel(
                    Align.center("[dim]Goodbye[/dim]"),
                    border_style=C["muted"],
                    padding=(1, 2),
                ))
                break


def print_version():
    console.print(f"Password Manager v{VERSION}")
    console.print(f"  DB:  {Path(__file__).resolve().parent / DB_NAME}")
    console.print(f"  Key: {Path(__file__).resolve().parent / KEY_FILE}")


if __name__ == "__main__":
    if "--version" in sys.argv or "-v" in sys.argv:
        print_version()
        sys.exit(0)

    try:
        init_db()
        menu()
    except KeyboardInterrupt:
        console.print(f"\n [{C['muted']}]Goodbye[/]")
