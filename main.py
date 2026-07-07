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


console = Console()

DB_NAME = Path("vault.db")
KEY_FILE = Path("secret.key")

VERSION = "1.0.0"

STYLE_PRIMARY = "cyan"
STYLE_SUCCESS = "green"
STYLE_WARN = "yellow"
STYLE_ERROR = "red"


def load_or_create_key():
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()

    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    console.print(f"[{STYLE_SUCCESS}]✔ Encryption key generated[/{STYLE_SUCCESS}]")
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
        return f"[{STYLE_ERROR}]DECRYPT ERROR: invalid token[/{STYLE_ERROR}]"


def add_password():
    console.print(Panel("Add new credential", style=STYLE_PRIMARY))
    console.print(f"[dim]Enter [b]b[/b] to go back[/dim]")

    site = Prompt.ask(f"[bold {STYLE_WARN}]Site[/bold {STYLE_WARN}]")
    if not site.strip() or site.strip().lower() == "b":
        return

    username = Prompt.ask(f"[bold {STYLE_WARN}]Username[/bold {STYLE_WARN}]")
    if not username.strip() or username.strip().lower() == "b":
        return

    password = Prompt.ask(f"[bold {STYLE_WARN}]Password[/bold {STYLE_WARN}]", password=True)
    if not password.strip() or password.strip().lower() == "b":
        return

    encrypted = encrypt_password(password)

    with db() as conn:
        conn.execute(
            "INSERT INTO passwords (site, username, password) VALUES (?, ?, ?)",
            (site.strip(), username.strip(), encrypted),
        )

    console.print(f"[bold {STYLE_SUCCESS}]✔ Password saved securely[/bold {STYLE_SUCCESS}]")


def list_passwords():
    with db() as conn:
        cur = conn.execute(
            "SELECT id, site, username, password, created_at FROM passwords"
        )
        rows = cur.fetchall()

    if not rows:
        console.print(Panel("Vault is empty", style=STYLE_WARN))
    else:
        table = Table(
            title="Password Vault",
            box=box.ROUNDED,
            border_style=STYLE_PRIMARY,
        )

        table.add_column("ID", style=STYLE_PRIMARY)
        table.add_column("Site", style=STYLE_SUCCESS)
        table.add_column("Username", style=STYLE_WARN)
        table.add_column("Password", style=STYLE_ERROR)
        table.add_column("Created", style="magenta")

        for row in rows:
            table.add_row(str(row[0]), row[1], row[2], "********", row[4])

        console.print(table)

    Prompt.ask(f"[dim]Press Enter to go back[/dim]")


def menu():
    while True:
        console.print(
            Panel.fit(
                f"[bold {STYLE_PRIMARY}]PASSWORD MANAGER[/bold {STYLE_PRIMARY}]  [dim]v{VERSION}[/dim]\n\n"
                f"[{STYLE_SUCCESS}]1[/{STYLE_SUCCESS}] Add password\n"
                f"[{STYLE_SUCCESS}]2[/{STYLE_SUCCESS}] List passwords\n"
                f"[{STYLE_SUCCESS}]3[/{STYLE_SUCCESS}] Exit",
                border_style=STYLE_PRIMARY,
            )
        )

        choice = Prompt.ask("Select", choices=["1", "2", "3"])

        match choice:
            case "1":
                add_password()
            case "2":
                list_passwords()
            case "3":
                console.print(f"[bold {STYLE_ERROR}]Goodbye[/bold {STYLE_ERROR}]")
                break


def print_version():
    console.print(f"[bold {STYLE_PRIMARY}]Password Manager[/bold {STYLE_PRIMARY}] v{VERSION}")
    console.print(f"[dim]{Path(__file__).resolve().parent / DB_NAME}[/dim]")
    console.print(f"[dim]{Path(__file__).resolve().parent / KEY_FILE}[/dim]")


if __name__ == "__main__":
    if "--version" in sys.argv or "-v" in sys.argv:
        print_version()
        sys.exit(0)

    try:
        init_db()
        menu()
    except KeyboardInterrupt:
        console.print(f"\n[bold {STYLE_ERROR}]Goodbye[/bold {STYLE_ERROR}]")
