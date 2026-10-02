# pylint: disable=missing-function-docstring,unused-argument,redefined-outer-name,import-error,import-outside-toplevel,wrong-import-position,no-name-in-module,protected-access,use-implicit-booleaness-not-comparison,subprocess-run-check,too-few-public-methods,consider-using-from-import

"""Security regression tests for encryption-key file handling.

Covers:
  * key file created world/group-readable by a permissive umask (HIGH)
  * existing permissive key files never re-locked (HIGH)
  * symlink attacks on the key file: reading an attacker-chosen file as the
    key, or overwriting an attacker-chosen target with key material (HIGH)
  * unvalidated key file content causing raw tracebacks instead of a clear
    fail-closed error (MEDIUM)
  * non-regular files (directories, FIFOs) accepted as the key (MEDIUM)
  * generate_key_file() overwriting an existing key (MEDIUM)
"""

import os
import stat
import sys

import pytest
from cryptography.fernet import Fernet

from app.crypto.key_manager import (
    KeyFileError,
    generate_key_file,
    load_or_create_key,
)


def _mode(path) -> int:
    return stat.S_IMODE(os.lstat(path).st_mode)


def _with_umask(umask: int, fn):
    previous = os.umask(umask)
    try:
        return fn()
    finally:
        os.umask(previous)


def test_created_key_file_is_owner_only_with_worst_case_umask(key_file):
    """Regression: load_or_create_key() wrote the key with 0666 & ~umask."""
    key = _with_umask(0o000, load_or_create_key)
    assert key_file.exists()
    assert _mode(key_file) == 0o600
    Fernet(key)  # key is still valid


def test_existing_world_readable_key_is_relocked_on_load(key_file):
    """Regression: a 0644 key file stayed world-readable forever."""
    key = Fernet.generate_key()
    key_file.write_bytes(key)
    os.chmod(key_file, 0o644)

    loaded = load_or_create_key()

    assert loaded == key
    assert _mode(key_file) == 0o600


def test_symlinked_key_is_refused_and_target_untouched(key_file, tmp_path):
    """Regression: write_bytes()/read_bytes() followed symlinks (arbitrary
    file overwrite as the user, or attacker-chosen key material)."""
    target = tmp_path / "victim.txt"
    target.write_bytes(b"do-not-touch")
    key_file.symlink_to(target)

    with pytest.raises(KeyFileError):
        load_or_create_key()

    assert target.read_bytes() == b"do-not-touch"
    assert target.is_symlink() or target.exists()


def test_broken_symlink_key_is_refused(key_file, tmp_path):
    key_file.symlink_to(tmp_path / "does-not-exist")
    with pytest.raises(KeyFileError):
        load_or_create_key()


def test_key_file_directory_is_refused(key_file):
    key_file.mkdir()
    with pytest.raises(KeyFileError):
        load_or_create_key()


def test_fifo_key_file_is_refused_without_hanging(key_file):
    if not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"):
        pytest.skip("POSIX-only")
    os.mkfifo(key_file)
    with pytest.raises(KeyFileError):
        load_or_create_key()


@pytest.mark.parametrize("payload", [b"", b"not a real key", b"\x00" * 44])
def test_malformed_key_file_raises_clear_error(key_file, payload):
    """Regression: garbage key content surfaced as an unhandled ValueError."""
    key_file.write_bytes(payload)
    with pytest.raises(KeyFileError):
        load_or_create_key()


def test_generate_key_file_never_overwrites_existing_key(key_file):
    original = load_or_create_key()
    with pytest.raises(KeyFileError):
        generate_key_file()
    assert key_file.read_bytes() == original
    assert _mode(key_file) == 0o600


def test_generated_key_roundtrips_encryption(key_file):
    key = load_or_create_key()
    token = Fernet(key).encrypt(b"roundtrip")
    assert Fernet(load_or_create_key()).decrypt(token) == b"roundtrip"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions")
def test_key_file_not_group_or_world_accessible(key_file):
    key = load_or_create_key()
    assert _mode(key_file) & 0o077 == 0
    assert key and Fernet(key)
