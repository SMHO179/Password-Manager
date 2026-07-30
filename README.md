# Password Manager

A CLI and GUI password manager for securely storing and managing credentials with end-to-end encryption.

## Features

- **Encrypted storage** — All passwords are encrypted with Fernet (AES-128-CBC) before being persisted to a local SQLite database.
- **Password generation** — Generates cryptographically secure random passwords of configurable length.
- **Strength checker** — Rates password strength (Weak, Medium, Strong, Very Strong) in real time.
- **Clipboard integration** — One-click copy to system clipboard via `pyperclip`.
- **Dual interface** — Terminal-based CLI with `rich` UI and a native PyQt6 GUI.
- **CRUD operations** — Add, list, edit, and delete credentials from the vault.

## Requirements

- Python 3.10+
- [SQLite3](https://www.sqlite.org/index.html) (bundled with Python)

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/SMohammad-Molanezhad/password-manager.git
cd password-manager
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For the GUI version:

```bash
pip install -r requirements-gui.txt
```

## Usage

### CLI

Run the interactive menu:

```bash
python main.py
```

Available options:
1. Add a new credential
2. List all stored credentials
3. Delete a credential by ID
4. Edit an existing credential
5. Generate a secure password
6. Exit

### Generate encryption key (first run only)

```bash
python generate_key.py
```

### GUI

```bash
python main_gui.py
```

## Project Structure

```
Password-Manager/
├── app/
│   ├── cli/              # Terminal UI (menus, prompts, panels)
│   ├── crypto/           # Fernet encryption & key management
│   ├── database/         # SQLite connection, queries, repository
│   ├── gui/              # PyQt6 GUI window and widgets
│   ├── services/         # Business logic (password gen & service)
│   └── utils/            # Clipboard, helpers, strength checker
├── main.py               # CLI entry point
├── main_gui.py           # GUI entry point
├── generate_key.py       # Standalone key generator
├── vault.db              # Encrypted credential store
├── secret.key            # Encryption key (not tracked in git)
└── requirements.txt      # Core dependencies
```

## Configuration

Settings are defined in `app/config.py`:

| Constant   | Purpose                          |
|------------|----------------------------------|
| `VERSION`  | Application version              |
| `DB_NAME`  | SQLite database file path        |
| `KEY_FILE` | Encryption key file path         |
| `STYLE`    | Rich terminal colour theme       |

Edit these values directly in that file.

## Security Notes

- The encryption key (`secret.key`) is stored in the working directory. **Back it up securely** — losing it makes stored passwords irrecoverable.
- Add `secret.key` and `vault.db` to `.gitignore` before sharing the repository.
- The key file permissions are set to `0600` on Unix systems automatically.

## License

[MIT](LICENSE)