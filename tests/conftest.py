# pylint: disable=missing-function-docstring,unused-argument,redefined-outer-name,import-error,import-outside-toplevel,wrong-import-position,no-name-in-module,protected-access,use-implicit-booleaness-not-comparison,subprocess-run-check,too-few-public-methods,consider-using-from-import

"""Shared fixtures for the security regression test-suite.

Every fixture redirects the application's file locations into pytest's
temporary directory so tests can never touch a real vault or key file.
"""

import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.crypto import encryption, key_manager  # noqa: E402
from app.database import connection  # noqa: E402


def _close_connection() -> None:
    if connection._conn is not None:
        try:
            connection._conn.close()
        finally:
            connection._conn = None


@pytest.fixture
def key_file(tmp_path, monkeypatch):
    """Redirect the key file into the test's temporary directory."""
    path = tmp_path / "secret.key"
    monkeypatch.setattr(key_manager, "KEY_FILE", path)
    return path


@pytest.fixture
def db_file(tmp_path, monkeypatch):
    """Redirect the vault database into the test's temporary directory."""
    path = tmp_path / "vault.db"
    monkeypatch.setattr(connection, "DB_NAME", path)
    _close_connection()
    yield path
    _close_connection()


@pytest.fixture
def cipher(monkeypatch):
    """Initialise the global Fernet cipher with a fresh throwaway key."""
    monkeypatch.setattr(encryption, "_fernet", None)
    encryption.init_fernet(Fernet.generate_key())
    yield encryption
    monkeypatch.setattr(encryption, "_fernet", None)
