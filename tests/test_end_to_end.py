# pylint: disable=missing-function-docstring,unused-argument,redefined-outer-name,import-error,import-outside-toplevel,wrong-import-position,no-name-in-module,protected-access,use-implicit-booleaness-not-comparison,subprocess-run-check,too-few-public-methods,consider-using-from-import

"""End-to-end functionality tests: the security fixes must not break the app.

Covers full CLI startup (key generation, DB creation, menu exit), permissions
of the files it creates, and the service-level CRUD roundtrip.
"""

import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _mode(path) -> int:
    return stat.S_IMODE(os.lstat(path).st_mode)


def test_cli_starts_exits_and_creates_hardened_files(tmp_path):
    """Full startup: fresh key + fresh vault, then clean exit from the menu."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py")],
        input="6\n",
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Goodbye" in result.stdout

    key_file = tmp_path / "secret.key"
    vault = tmp_path / "vault.db"
    assert key_file.exists() and vault.exists()
    assert _mode(key_file) == 0o600
    assert _mode(vault) == 0o600
    # No key material may be echoed to the console or stderr.
    key_material = key_file.read_bytes()
    assert key_material.decode() not in result.stdout
    assert key_material.decode() not in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_add_then_list_roundtrip(tmp_path):
    """Add a credential through the real prompts, then list it back."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py")],
        input="1\nexample-site.test\nalice-user\nCorrectHorse!42\n\n2\n\n6\n",
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Saved securely" in result.stdout
    assert "example-site.test" in result.stdout
    assert "alice-user" in result.stdout
    # The stored password must never be echoed (list shows no passwords).
    assert "CorrectHorse!42" not in result.stdout
    assert "Traceback" not in result.stderr


def test_cli_survives_existing_world_readable_key(tmp_path):
    """A legacy 0644 key file is usable and gets re-locked, not rejected."""
    from cryptography.fernet import Fernet

    key = Fernet.generate_key()
    key_file = tmp_path / "secret.key"
    key_file.write_bytes(key)
    os.chmod(key_file, 0o644)

    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py")],
        input="6\n",
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr
    assert _mode(key_file) == 0o600


def test_cli_garbage_key_fails_closed_with_clear_error(tmp_path):
    """A corrupted key file must stop the app with a readable error."""
    (tmp_path / "secret.key").write_bytes(b"garbage")
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py")],
        input="6\n",
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=60,
    )
    assert result.returncode == 1
    assert "Encryption key error" in result.stdout
    assert "Traceback" not in result.stderr


def test_cli_symlinked_key_is_refused(tmp_path):
    victim = tmp_path / "victim.txt"
    victim.write_bytes(b"do-not-touch")
    (tmp_path / "secret.key").symlink_to(victim)

    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py")],
        input="6\n",
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=60,
    )
    assert result.returncode == 1
    assert "Encryption key error" in result.stdout
    assert victim.read_bytes() == b"do-not-touch"


def test_service_crud_roundtrip(db_file, cipher):
    """Repository/service behaviour is unchanged by the security fixes."""
    from app.database.connection import init_db
    from app.database.repository import Repository
    from app.services.password_service import PasswordService

    init_db()
    service = PasswordService(Repository())

    assert service.list_all() == []
    service.add("site-a", "user-a", "pw-a")
    service.add("site-b", "user-b", "pw-b")
    rows = service.list_all()
    assert len(rows) == 2
    # list_all() is ordered by id DESC; resolve the id of site-a explicitly.
    ids = {row[1]: row[0] for row in rows}
    first_id = ids["site-a"]

    assert service.get_details(first_id) == ("site-a", "user-a", "pw-a")

    assert service.update(first_id, "site-a2", "user-a2", "pw-a2") is True
    assert service.get_details(first_id) == ("site-a2", "user-a2", "pw-a2")

    assert service.delete(first_id) is True
    assert service.delete(99999) is False
    assert len(service.list_all()) == 1


def test_passwords_stored_encrypted_at_rest(db_file, cipher):
    """Plaintext passwords must never be readable from vault.db."""
    from app.database import connection
    from app.database.connection import init_db
    from app.database.repository import Repository
    from app.services.password_service import PasswordService

    init_db()
    service = PasswordService(Repository())
    service.add("site-a", "user-a", "TopSecretPlaintext-XYZ")

    with connection.db() as conn:
        rows = conn.execute("SELECT password FROM passwords").fetchall()
    assert rows
    for (token,) in rows:
        assert "TopSecretPlaintext-XYZ" not in token
        assert token.startswith("gAAAAA")
