import sys
import sqlite3
import string
import random

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


console = Console()

DB_NAME = Path("vault.db")
KEY_FILE = Path("secret.key")

VERSION = "1.3.0"

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

def check_password_strength(password: str):
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

    elif score <= 4:
        return "Medium", "yellow"

    elif score == 5:
        return "Strong", "green"

    else:
        return "Very Strong", "bright_green"

def load_or_create_key():
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()

    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)

    console.print(
        "[green]✔ Encryption key generated[/green]"
    )

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
    return fernet.encrypt(
        password.encode()
    ).decode()


def decrypt_password(password):
    try:
        return fernet.decrypt(
            password.encode()
        ).decode()

    except InvalidToken:
        return ""


def ask_back(text, password=False):
    value = Prompt.ask(
        text,
        password=password
    )

    if value.lower() == "b":
        return None

    return value


def generate_password():
    console.print(
        Panel(
            "[bold]Password Generator[/bold]",
            border_style=C["border"]
        )
    )

    length = Prompt.ask(
        "Length",
        default="16"
    )

    try:
        length = int(length)
    except ValueError:
        length = 16

    if length < 4:
        length = 4

    chars = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(chars) for _ in range(length))

    console.print(
        f"\nGenerated password:\n[bold cyan]{password}[/bold cyan]"
    )

    copy = Prompt.ask(
        "Copy to clipboard?",
        choices=["y", "n"],
        default="y"
    )

    if copy.lower() == "y":
        try:
            import pyperclip
            pyperclip.copy(password)
            console.print("[green]✔ Copied to clipboard[/green]")
        except ImportError:
            console.print("[yellow]pyperclip not installed. Select and copy manually.[/yellow]")

    pause()


def pause():
    Prompt.ask(
        "\nPress Enter to return to menu",
        default=""
    )


def add_password():

    console.print(
        Panel(
            "[bold]New Credential[/bold]",
            border_style=C["border"]
        )
    )

    site = ask_back("Site")
    if site is None:
        return

    username = ask_back("Username")
    if username is None:
        return

    password = ask_back(
        "Password",
        password=True
    )
    
    strength, color = check_password_strength(password)
    
    console.print(
        f"Password strength: [{color}]{strength}[/{color}]"
    )
    if password is None:
        return

    encrypted = encrypt_password(password)

    with db() as conn:
        conn.execute(
            """
            INSERT INTO passwords(
                site,
                username,
                password
            )
            VALUES (?, ?, ?)
            """,
            (
                site,
                username,
                encrypted
            )
        )

    console.print(
        "[green]✔ Saved securely[/green]"
    )

    pause()


def list_passwords():

    with db() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                site,
                username,
                created_at
            FROM passwords
            ORDER BY id DESC
            """
        ).fetchall()


    if not rows:
        console.print(
            "[yellow]No passwords found[/yellow]"
        )

        pause()
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

    pause()


def delete_password():

    list_passwords()

    entry_id = ask_back(
        "ID to delete"
    )

    if entry_id is None:
        return


    with db() as conn:

        result = conn.execute(
            """
            DELETE FROM passwords
            WHERE id=?
            """,
            (entry_id,)
        )


    if result.rowcount:
        console.print(
            "[red]✔ Deleted[/red]"
        )

    else:
        console.print(
            "[yellow]ID not found[/yellow]"
        )


    pause()


def edit_password():

    list_passwords()

    entry_id = ask_back(
        "ID to edit"
    )

    if entry_id is None:
        return


    new_site = ask_back(
        "New site"
    )

    if new_site is None:
        return


    new_username = ask_back(
        "New username"
    )

    if new_username is None:
        return


    new_password = ask_back(
        "New password",
        password=True
    )

    if new_password is None:
        return


    encrypted = encrypt_password(
        new_password
    )


    with db() as conn:

        result = conn.execute(
            """
            UPDATE passwords
            SET
                site=?,
                username=?,
                password=?
            WHERE id=?
            """,
            (
                new_site,
                new_username,
                encrypted,
                entry_id
            )
        )


    if result.rowcount:
        console.print(
            "[yellow]✔ Updated[/yellow]"
        )

    else:
        console.print(
            "[red]ID not found[/red]"
        )


    pause()


def menu():

    while True:

        console.print(
            Panel(
                Align.center(
                    Text(
                        "PASSWORD MANAGER",
                        style=C["header"]
                    )
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
[green]5[/] Generate password
[green]6[/] Exit

[dim]Type b anytime to return[/dim]
        """)


        choice = Prompt.ask(
            "Select",
            choices=[
                "1",
                "2",
                "3",
                "4",
                "5",
                "6"
            ]
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
            generate_password()

        elif choice == "6":
            console.print(
                "[cyan]Goodbye[/cyan]"
            )

            break



def print_version():

    console.print(
        f"Password Manager v{VERSION}"
    )



if __name__ == "__main__":

    if "--version" in sys.argv:
        print_version()
        sys.exit()


    try:

        init_db()
        menu()


    except KeyboardInterrupt:

        console.print(
            "\n[dim]Goodbye[/dim]"
        )
