"""Database connection management."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

from app.config import DB_NAME
from app.database.queries import SQL_CREATE_TABLE


@contextmanager
def db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for a SQLite connection with auto-commit/rollback."""
    conn = sqlite3.connect(str(DB_NAME))
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create the passwords table if it does not exist."""
    with db() as conn:
        conn.execute(SQL_CREATE_TABLE)
