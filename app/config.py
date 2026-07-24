"""Application configuration constants."""

from pathlib import Path

VERSION = "1.3.0"
DB_NAME = Path("vault.db")
KEY_FILE = Path("secret.key")

STYLE = {
    "primary": "cyan",
    "success": "green",
    "warn": "yellow",
    "error": "red",
    "muted": "bright_black",
    "accent": "magenta",
    "header": "bold cyan",
    "border": "cyan",
}
