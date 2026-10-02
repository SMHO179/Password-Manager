# pylint: disable=missing-function-docstring,unused-argument,redefined-outer-name,import-error,import-outside-toplevel,wrong-import-position,no-name-in-module,protected-access,use-implicit-booleaness-not-comparison,subprocess-run-check,too-few-public-methods,consider-using-from-import

"""Security regression tests for vault integrity (authenticated decryption).

Covers:
  * decrypt_password() silently returning "" for tampered/invalid tokens,
    making a integrity failure indistinguishable from a real empty
    password (MEDIUM)
  * PasswordService.get_details() hiding tampering from its callers (MEDIUM)
"""

import pytest
from cryptography.fernet import Fernet

from app.crypto.encryption import (
    DecryptionError,
    EncryptionError,
    decrypt_password,
    encrypt_password,
    init_fernet,
)
from app.database import connection
from app.database.connection import init_db
from app.database.repository import Repository
from app.services.password_service import PasswordService


def test_roundtrip(cipher):
    assert decrypt_password(encrypt_password("hunter2")) == "hunter2"


def test_tampered_token_raises_instead_of_returning_empty(cipher):
    """Regression: InvalidToken used to be swallowed as ''."""
    token = encrypt_password("real-password")
    tampered = token[:-4] + "AAAA"
    with pytest.raises(DecryptionError):
        decrypt_password(tampered)


def test_token_encrypted_with_other_key_raises(cipher):
    token = encrypt_password("real-password")
    init_fernet(Fernet.generate_key())
    with pytest.raises(DecryptionError):
        decrypt_password(token)


def test_truncated_token_raises(cipher):
    token = encrypt_password("real-password")
    with pytest.raises(DecryptionError):
        decrypt_password(token[:20])


def test_garbage_token_raises(cipher):
    with pytest.raises(DecryptionError):
        decrypt_password("not-a-fernet-token")


@pytest.mark.parametrize("bad", ["", None, 123, b"bytes-are-wrong"])
def test_missing_or_malformed_token_raises(cipher, bad):
    with pytest.raises(DecryptionError):
        decrypt_password(bad)


def test_uninitialised_cipher_fails_closed():
    import app.crypto.encryption as encryption

    saved = encryption._fernet
    encryption._fernet = None
    try:
        with pytest.raises(EncryptionError):
            encrypt_password("x")
        with pytest.raises(EncryptionError):
            decrypt_password("x")
    finally:
        encryption._fernet = saved


def test_service_surfaces_tampering_end_to_end(db_file, cipher):
    """A tampered vault row must raise, not hand back an empty password."""
    init_db()
    service = PasswordService(Repository())
    service.add("example.com", "alice", "correct-horse-battery")
    entry_id = service.list_all()[0][0]

    # Sanity: untampered roundtrip still works.
    details = service.get_details(entry_id)
    assert details is not None
    assert details[2] == "correct-horse-battery"

    # Tamper with the ciphertext at rest (no key required for an attacker
    # with write access to vault.db).
    with connection.db() as conn:
        conn.execute(
            "UPDATE passwords SET password = ? WHERE id = ?",
            ("gAAAAAcrippedciphertextAAAAAAAAAAAAAAAAAAAAAAAA", entry_id),
        )

    with pytest.raises(DecryptionError):
        service.get_details(entry_id)


def test_service_detects_key_mismatch_end_to_end(db_file, cipher):
    init_db()
    service = PasswordService(Repository())
    service.add("example.com", "alice", "correct-horse-battery")
    entry_id = service.list_all()[0][0]

    init_fernet(Fernet.generate_key())  # wrong key loaded

    with pytest.raises(DecryptionError):
        service.get_details(entry_id)
