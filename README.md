# Password Manager

A secure CLI password manager built with Python. Passwords are encrypted with AES (Fernet) and stored in a local SQLite database.

## Features

- AES-256 encryption via Fernet (symmetric cryptography)
- Local SQLite storage — no cloud, no network
- Interactive terminal UI powered by Rich
- Auto-generated encryption key on first run
- Password masking during input
- Input validation (empty fields rejected)
- Graceful Ctrl+C handling
- Atomic database transactions with auto-rollback on error

## Technologies

- **Python 3.14+**
- **SQLite3** — embedded database
- **cryptography** — Fernet (AES-256-CBC with HMAC)
- **rich** — terminal UI framework

## Project Structure

```
.
├── main.py           # Application entry point
├── generate_key.py   # Standalone key generator (optional)
├── secret.key        # Encryption key (auto-generated, keep safe!)
├── vault.db          # SQLite password database
├── requirements.txt  # Python dependencies
├── README.md         # Persian documentation
├── README-EN.md      # English documentation
└── LICENSE
```

## Usage

### 1. Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate encryption key (optional — auto-generated on first run)

```bash
python generate_key.py
```

### 3. Run

```bash
python main.py
```

### Menu

```
1. Add password
2. List passwords
3. Exit
```

## Security

- **Passwords are never stored in plaintext** — encrypted before writing to disk
- **Unique encryption key** — each vault gets its own `secret.key`
- **Key is required for decryption** — without it, the vault is unrecoverable
- **Input is masked** — passwords are hidden during entry
- **Empty inputs rejected** — no silent failures

> **Warning:** Losing `secret.key` means permanent data loss. Back it up securely.

## Database Schema

| Column      | Type      | Description                |
|-------------|-----------|----------------------------|
| id          | INTEGER   | Primary key (auto-increment) |
| site        | TEXT      | Website or service name    |
| username    | TEXT      | Login username             |
| password    | TEXT      | Fernet-encrypted password  |
| created_at  | TIMESTAMP | Auto-generated insert time |

## License

See [LICENSE](LICENSE).
