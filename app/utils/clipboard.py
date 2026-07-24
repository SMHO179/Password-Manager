"""Clipboard utilities."""


def copy_to_clipboard(text: str) -> bool:
    """Copy text to the system clipboard.

    Returns True on success, False when ``pyperclip`` is not available.
    """
    try:
        import pyperclip  # noqa: PLC0415

        pyperclip.copy(text)
        return True
    except ImportError:
        return False
