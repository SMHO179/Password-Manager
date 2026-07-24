"""Data access repository for password credentials."""

from app.database.connection import db
from app.database.queries import (
    SQL_DELETE_PASSWORD,
    SQL_INSERT_PASSWORD,
    SQL_SELECT_PASSWORD_BY_ID,
    SQL_SELECT_PASSWORDS,
    SQL_UPDATE_PASSWORD,
)


class Repository:
    """Handles all database operations for password records.

    Every public method opens a fresh connection so the caller never has to
    manage transactions manually.
    """

    def get_all(self) -> list[tuple]:
        """Retrieve all password summaries (id, site, username, created_at)."""
        with db() as conn:
            return conn.execute(SQL_SELECT_PASSWORDS).fetchall()

    def get_by_id(self, entry_id: int) -> tuple | None:
        """Retrieve a single record by id (site, username, encrypted_password)."""
        with db() as conn:
            return conn.execute(
                SQL_SELECT_PASSWORD_BY_ID, (entry_id,)
            ).fetchone()

    def add(self, site: str, username: str, encrypted_password: str) -> None:
        """Insert a new password record."""
        with db() as conn:
            conn.execute(
                SQL_INSERT_PASSWORD, (site, username, encrypted_password)
            )

    def delete(self, entry_id: int) -> bool:
        """Delete a record by id. Returns True if a row was removed."""
        with db() as conn:
            result = conn.execute(SQL_DELETE_PASSWORD, (entry_id,))
        return result.rowcount > 0

    def update(
        self,
        entry_id: int,
        site: str,
        username: str,
        encrypted_password: str,
    ) -> bool:
        """Update a record by id. Returns True if a row was updated."""
        with db() as conn:
            result = conn.execute(
                SQL_UPDATE_PASSWORD,
                (site, username, encrypted_password, entry_id),
            )
        return result.rowcount > 0
