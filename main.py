import sqlite3
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from cryptography.fernet import Fernet

console = Console()

DB_NAME = "vault.db"
KEY_FILE = "secret.key"

# ------------------ LOAD KEY ------------------

def load_key():
    return open(KEY_FILE, "rb").read()

fernet = Fernet(load_key())

# ------------------ DB ------------------

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# ------------------ ENCRYPT ------------------

def encrypt_password(password: str) -> str:
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(password: str) -> str:
    return fernet.decrypt(password.encode()).decode()

# ------------------ ADD ------------------

def add_password():
    site = Prompt.ask("Site")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)

    encrypted = encrypt_password(password)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO passwords (site, username, password) VALUES (?, ?, ?)",
        (site, username, encrypted)
    )

    conn.commit()
    conn.close()

    console.print("[green]✔ Saved encrypted password![/green]")

# ------------------ LIST ------------------

def list_passwords():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, site, username, password, created_at FROM passwords")
    rows = cur.fetchall()

    table = Table(title="Vault (Decrypted View)")

    table.add_column("ID")
    table.add_column("Site")
    table.add_column("Username")
    table.add_column("Password")
    table.add_column("Created")

    for row in rows:
        decrypted = decrypt_password(row[3])

        table.add_row(
            str(row[0]),
            row[1],
            row[2],
            decrypted,
            str(row[4])
        )

    console.print(table)
    conn.close()
# ------------------ DELETE ------------------
def delete_password():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, site, username FROM passwords")
    rows = cur.fetchall()

    table = Table(title="Select Entry To Delete")
    table.add_column("ID")
    table.add_column("Site")
    table.add_column("Username")
    for row in rows:
        table.add_row(str(row[0]), row[1], row[2])
    console.print(table)

    entry_id = Prompt.ask("Enter ID to delete")
    cur.execute("DELETE FROM passwords WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    console.print("[red]✔ Entry deleted![/red]")


# ------------------ EDIT ------------------
def edit_password():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, site, username FROM passwords")
    rows = cur.fetchall()

    table = Table(title="Select Entry To Edit")
    table.add_column("ID")
    table.add_column("Site")
    table.add_column("Username")
    for row in rows:
        table.add_row(str(row[0]), row[1], row[2])
    console.print(table)

    entry_id = Prompt.ask("Enter ID to edit")
    new_site = Prompt.ask("New Site")
    new_username = Prompt.ask("New Username")
    new_password = Prompt.ask("New Password", password=True)
    encrypted = encrypt_password(new_password)

    cur.execute(
        "UPDATE passwords SET site = ? username = ? password = ? WHERE id = ?",
        (new_site, new_username, encrypted, entry_id)
    )
    conn.commit()
    conn.close()
    console.print("[yellow]✔ Entry updated![/yellow]")


# ------------------ MENU ------------------
def menu():
    while True:
        console.print("\n[bold cyan]=== PASSWORD MANAGER ===[/bold cyan]")
        console.print("1) Add password")
        console.print("2) List passwords")
        console.print("3) Delete password")
        console.print("4) Edit password")
        console.print("5) Exit")

        choice = Prompt.ask("Choose", choices=["1", "2", "3", "4", "5"])

        if choice == "1":
            add_password()
        elif choice == "2":
            list_passwords()
        elif choice == "3":
            delete_password()
        elif choice == "4":
            edit_password()
        else:
            break

    menu()
