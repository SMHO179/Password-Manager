"""Rich panel helpers for the CLI."""

from rich.panel import Panel

from app.config import STYLE


def make_section_panel(title: str) -> Panel:
    """Create a section heading panel with the standard border style."""
    return Panel(f"[bold]{title}[/bold]", border_style=STYLE["border"])
