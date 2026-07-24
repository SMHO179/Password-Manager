"""CLI menu and dispatch logic."""

from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt

from app.cli import console
from app.cli.panels import make_section_panel
from app.cli.prompts import pause, prompt_or_back
from app.config import STYLE, VERSION
from app.services.password_generator import generate_password
from app.services.password_service import PasswordService
from app.utils.clipboard import copy_to_clipboard
from app.utils.password_strength import check_password_strength


def add_password(service: PasswordService) -> None:
    """Prompt for a new credential and store it encrypted."""
    console.print(make_section_panel("New Credential"))

    site = prompt_or_back("Site")
    if site is None:
        return

    username = prompt_or_back("Username")
    if username is None:
        return

    password = prompt_or_back("Password", password=True)

    strength, color = check_password_strength(password)
    console.print(f"Password strength: [{color}]{strength}[/{color}]")
    if password is None:
        return

    service.add(site, username, password)

    console.print("[green]✔ Saved securely[/green]")
    pause()


def list_passwords(service: PasswordService) -> None:
    """Display all stored credentials in a table."""
    rows = service.list_all()

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


def delete_password(service: PasswordService) -> None:
    """List passwords and remove the one chosen by ID."""
    list_passwords(service)

    entry_id = prompt_or_back("ID to delete")
    if entry_id is None:
        return

    if service.delete(entry_id):
        console.print("[red]✔ Deleted[/red]")
    else:
        console.print("[yellow]ID not found[/yellow]")

    pause()


def edit_password(service: PasswordService) -> None:
    """List passwords and update the one chosen by ID with new values."""
    list_passwords(service)

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

    if service.update(entry_id, new_site, new_username, new_password):
        console.print("[yellow]✔ Updated[/yellow]")
    else:
        console.print("[red]ID not found[/red]")

    pause()


def handle_generate_password() -> None:
    """Generate a random password with a user-chosen length."""
    console.print(make_section_panel("Password Generator"))

    length = Prompt.ask("Length", default="16")
    try:
        length = int(length)
    except ValueError:
        length = 16

    if length < 4:
        length = 4

    password = generate_password(length)

    console.print(f"\nGenerated password:\n[bold cyan]{password}[/bold cyan]")

    copy = Prompt.ask("Copy to clipboard?", choices=["y", "n"], default="y")
    if copy.lower() == "y":
        if copy_to_clipboard(password):
            console.print("[green]✔ Copied to clipboard[/green]")
        else:
            console.print(
                "[yellow]pyperclip not installed. "
                "Select and copy manually.[/yellow]"
            )

    pause()


def print_version() -> None:
    """Print the application version."""
    console.print(f"Password Manager v{VERSION}")


def menu(service: PasswordService) -> None:
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
                add_password(service)
            case "2":
                list_passwords(service)
            case "3":
                delete_password(service)
            case "4":
                edit_password(service)
            case "5":
                handle_generate_password()
            case "6":
                console.print("[cyan]Goodbye[/cyan]")
                break
