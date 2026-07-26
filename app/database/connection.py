"""Database connection management."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

from app.config import DB_NAME
from app.database.queries import SQL_CREATE_TABLE

_conn: sqlite3.Connection | None = None


@contextmanager
def db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for a persistent SQLite connection with auto-commit/rollback."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_NAME))
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
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
