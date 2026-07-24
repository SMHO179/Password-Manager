"""CLI prompt utilities."""

from rich.prompt import Prompt


def prompt_or_back(text: str, *, password: bool = False) -> str | None:
    """Prompt for input; return None when the user types 'b' to go back."""
    value = Prompt.ask(text, password=password)
    return None if value.lower() == "b" else value


def pause() -> None:
    """Wait for Enter before returning to the menu."""
    Prompt.ask("\nPress Enter to return to menu", default="")
