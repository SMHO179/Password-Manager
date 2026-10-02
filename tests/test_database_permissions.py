# pylint: disable=missing-function-docstring,unused-argument,redefined-outer-name,import-error,import-outside-toplevel,wrong-import-position,no-name-in-module,protected-access,use-implicit-booleaness-not-comparison,subprocess-run-check,too-few-public-methods,consider-using-from-import

"""Security regression tests for vault database file permissions.

Covers:
  * vault.db created world-readable (0666 & ~umask) (HIGH)
  * WAL/SHM sidecars inheriting world-readable permissions (HIGH)
  * pre-existing permissive databases never re-locked (HIGH)
"""

import os
import stat
import sqlite3

import pytest

from app.database import connection
from app.database.connection import init_db


def _mode(path) -> int | None:
    if os.path.lexists(path):
        return stat.S_IMODE(os.stat(path).st_mode)
    return None


def _sidecars(db_path):
    for suffix in ("-wal", "-shm"):
        yield str(db_path) + suffix


def test_new_database_is_owner_only(db_file, monkeypatch):
    """Regression: sqlite3.connect() created vault.db with 0644."""
    previous = os.umask(0o000)  # worst case: no umask protection at all
    try:
        init_db()
    finally:
        os.umask(previous)
    assert _mode(db_file) == 0o600


def test_wal_and_shm_sidecars_are_owner_only(db_file):
    init_db()
    with connection.db() as conn:
        conn.execute(
            "INSERT INTO passwords(site, username, password) VALUES (?, ?, ?)",
            ("example.com", "alice", "gAAAAA-token"),
        )
    for sidecar in _sidecars(db_file):
        # Sidecars exist while the connection is open (WAL mode).
        assert _mode(sidecar) == 0o600, sidecar


def test_existing_world_readable_database_is_relocked(db_file):
    """Regression: a pre-existing 0644 vault.db was never chmod'ed."""
    conn = sqlite3.connect(db_file)
    conn.execute(
        "CREATE TABLE passwords(id INTEGER PRIMARY KEY, site TEXT,"
        " username TEXT, password TEXT)"
    )
    conn.commit()
    conn.close()
    os.chmod(db_file, 0o644)

    init_db()

    assert _mode(db_file) == 0o600
    with connection.db() as conn:
        conn.execute(
            "INSERT INTO passwords(site, username, password) VALUES (?, ?, ?)",
            ("s", "u", "t"),
        )
    for sidecar in _sidecars(db_file):
        assert _mode(sidecar) == 0o600, sidecar


@pytest.mark.parametrize("umask", [0o000, 0o022, 0o007])
def test_permissions_hold_under_any_umask(db_file, umask):
    previous = os.umask(umask)
    try:
        init_db()
        with connection.db() as conn:
            conn.execute(
                "INSERT INTO passwords(site, username, password)"
                " VALUES (?, ?, ?)",
                ("s", "u", "t"),
            )
    finally:
        os.umask(previous)
    assert _mode(db_file) == 0o600
    for sidecar in _sidecars(db_file):
        assert _mode(sidecar) == 0o600, sidecar


def test_database_not_group_or_world_accessible(db_file):
    init_db()
    assert (_mode(db_file) or 0) & 0o077 == 0
