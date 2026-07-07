from pathlib import Path
import os
import stat

from cryptography.fernet import Fernet
from rich.console import Console
from rich.panel import Panel


console = Console()

KEY_FILE = Path("secret.key")


def generate_key():

    if KEY_FILE.exists():
        console.print(
            Panel(
                "Key already exists!\n"
                "Generating a new key will destroy access to existing passwords.",
                title="Warning",
                border_style="red"
            )
        )
        return


    key = Fernet.generate_key()

    KEY_FILE.write_bytes(key)


    # Linux/macOS: owner read-only permission
    try:
        os.chmod(
            KEY_FILE,
            stat.S_IRUSR | stat.S_IWUSR
        )

    except PermissionError:
        pass


    console.print(
        Panel(
            "Encryption key created successfully\n"
            f"Location: {KEY_FILE.absolute()}",
            title="Success",
            border_style="green"
        )
    )


if __name__ == "__main__":
    generate_key()
