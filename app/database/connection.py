"""Database connection management with hardened file permissions."""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

from app.config import DB_NAME
from app.database.queries import SQL_CREATE_TABLE

_DB_MODE = 0o600

_conn: sqlite3.Connection | None = None


def _create_db_file() -> None:
    """Create the database file with owner-only permissions if missing.

    SQLite creates new databases with mode 0666 & ~umask (world-readable by
    default), so the file is created here first; SQLite then reuses it and
    its WAL/SHM sidecars inherit these permissions.
    """
    if os.path.lexists(DB_NAME):
        return
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        fd = os.open(DB_NAME, flags, _DB_MODE)
        os.close(fd)
    except OSError:
        # Raced with another creator, or cannot create (symlink/planted file);
        # opening below will surface any real problem.
        return


def _ensure_db_permissions() -> None:
    """Force owner-only permissions on the database and its WAL/SHM files.

    Silently skipped on platforms without the required POSIX calls.
    """
    if not (hasattr(os, "O_NOFOLLOW") and hasattr(os, "fchmod")):
        return
    for name in (str(DB_NAME), f"{DB_NAME}-wal", f"{DB_NAME}-shm"):
        if not os.path.lexists(name):
            continue
        try:
            fd = os.open(
                name,
                os.O_RDWR | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
            )
        except OSError:
            # Symlink or unreadable file: leave it alone; sqlite will fail
            # loudly if the database itself is unusable.
            continue
        try:
            os.fchmod(fd, _DB_MODE)
        except OSError:
            pass
        finally:
            os.close(fd)


@contextmanager
def db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for a persistent SQLite connection with auto-commit/rollback.

    File permissions are set before the first connection so that the
    database and every WAL/SHM sidecar SQLite creates from it are
    owner-readable/writable only.
    """
    global _conn
    if _conn is None:
        _create_db_file()
        _ensure_db_permissions()
        _conn = sqlite3.connect(str(DB_NAME))
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
        _ensure_db_permissions()
    try:
        yield _conn
        _conn.commit()
    except Exception:
        _conn.rollback()
        raise


def init_db() -> None:
    """Create the passwords table if it does not exist."""
    with db() as conn:
        conn.execute(SQL_CREATE_TABLE)
