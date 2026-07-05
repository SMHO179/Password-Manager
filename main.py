import sqlite3
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()

DB_NAME = "vault.db"

# ------------------ CONNECTION ------------------

def get_connection():
    return sqlite3.connect(DB_NAME)

# ------------------ INIT DB ------------------

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

# ------------------ ADD PASSWORD ------------------

def add_password():
    site = Prompt.ask("Site")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO passwords (site, username, password) VALUES (?, ?, ?)",
            (site, username, password)
        )

        conn.commit()
        console.print("[green]✔ Saved successfully![/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

    finally:
        conn.close()

# ------------------ LIST PASSWORDS ------------------

def list_passwords():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, site, username, password, created_at FROM passwords")
    rows = cur.fetchall()

    table = Table(title="Vault")

    table.add_column("ID", style="cyan")
    table.add_column("Site", style="magenta")
    table.add_column("Username", style="green")
    table.add_column("Password", style="red")
    table.add_column("Created At", style="yellow")

    for row in rows:
        table.add_row(str(row[0]), row[1], row[2], row[3], str(row[4]))

    console.print(table)
    conn.close()

# ------------------ MENU ------------------

def menu():
    while True:
        console.print("\n[bold cyan]=== PASSWORD MANAGER ===[/bold cyan]")
        console.print("1) Add password")
        console.print("2) List passwords")
        console.print("3) Exit")

        choice = Prompt.ask("Choose", choices=["1", "2", "3"])

        if choice == "1":
            add_password()
        elif choice == "2":
            list_passwords()
        else:
            break

# ------------------ MAIN ------------------

if __name__ == "__main__":
    init_db()
    menu()
