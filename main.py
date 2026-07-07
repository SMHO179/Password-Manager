import sqlite3
from pathlib import Path
from contextlib import contextmanager

from cryptography.fernet import Fernet

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich import box


console = Console()


DB_NAME = Path("vault.db")
KEY_FILE = Path("secret.key")


# ======================
# KEY MANAGEMENT
# ======================

def load_or_create_key():
    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
        console.print("[green]✔ Encryption key generated[/green]")

    return KEY_FILE.read_bytes()


fernet = Fernet(load_or_create_key())


# ======================
# DATABASE
# ======================

@contextmanager
def db():
    conn = sqlite3.connect(DB_NAME)

    try:
        yield conn
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

        conn.commit()


# ======================
# CRYPTO
# ======================

def encrypt_password(password):
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(password):

    try:
        return fernet.decrypt(password.encode()).decode()

    except Exception:
        return "[red]DECRYPT ERROR[/red]"



# ======================
# ACTIONS
# ======================

def add_password():

    console.print(
        Panel(
            "Add new credential",
            style="cyan"
        )
    )


    site = Prompt.ask(
        "[bold yellow]Site[/bold yellow]"
    )

    username = Prompt.ask(
        "[bold yellow]Username[/bold yellow]"
    )

    password = Prompt.ask(
        "[bold yellow]Password[/bold yellow]",
        password=True
    )


    encrypted = encrypt_password(password)


    with db() as conn:

        conn.execute(
            """
            INSERT INTO passwords
            (site, username, password)
            VALUES (?, ?, ?)
            """,
            (
                site,
                username,
                encrypted
            )
        )

        conn.commit()


    console.print(
        "[bold green]✔ Password saved securely[/bold green]"
    )



def list_passwords():

    with db() as conn:

        rows = conn.execute(
            """
            SELECT id, site, username, password, created_at
            FROM passwords
            """
        ).fetchall()


    if not rows:
        console.print(
            Panel(
                "Vault is empty",
                style="yellow"
            )
        )
        return


    table = Table(
        title="Password Vault",
        box=box.ROUNDED,
        border_style="cyan"
    )


    table.add_column(
        "ID",
        style="cyan"
    )

    table.add_column(
        "Site",
        style="green"
    )

    table.add_column(
        "Username",
        style="yellow"
    )

    table.add_column(
        "Password",
        style="red"
    )

    table.add_column(
        "Created",
        style="magenta"
    )


    for row in rows:

        table.add_row(
            str(row[0]),
            row[1],
            row[2],
            "********",
            row[4]
        )


    console.print(table)


# ======================
# UI
# ======================

def menu():

    while True:

        console.print(
            Panel.fit(
                "[bold cyan]PASSWORD MANAGER[/bold cyan]\n\n"
                "[green]1[/green] Add password\n"
                "[green]2[/green] List passwords\n"
                "[green]3[/green] Exit",
                border_style="cyan"
            )
        )


        choice = Prompt.ask(
            "Select",
            choices=[
                "1",
                "2",
                "3"
            ]
        )


        match choice:

            case "1":
                add_password()

            case "2":
                list_passwords()

            case "3":
                console.print(
                    "[bold red]Goodbye[/bold red]"
                )
                break



if __name__ == "__main__":

    init_db()
    menu()
