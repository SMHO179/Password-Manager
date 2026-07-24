"""High-level password management service."""

from app.crypto.encryption import decrypt_password, encrypt_password
from app.database.repository import Repository


class PasswordService:
    """Provides business-logic operations for password credentials.

    Encapsulates the coordination between encryption and data-access layers,
    exposing a simple interface for the UI layer to consume.
    """

    def __init__(self, repository: Repository | None = None):
        self._repo = repository or Repository()

    def add(self, site: str, username: str, plain_password: str) -> None:
        """Encrypt and store a new password credential."""
        encrypted = encrypt_password(plain_password)
        self._repo.add(site, username, encrypted)

    def list_all(self) -> list[tuple]:
        """Return all stored credential summaries (id, site, username, created_at)."""
        return self._repo.get_all()

    def delete(self, entry_id: int) -> bool:
        """Delete a credential by id. Returns True if a row was removed."""
        return self._repo.delete(entry_id)

    def update(
        self, entry_id: int, site: str, username: str, plain_password: str
    ) -> bool:
        """Update a credential. Returns True if a row was updated."""
        encrypted = encrypt_password(plain_password)
        return self._repo.update(entry_id, site, username, encrypted)

    def get_details(self, entry_id: int) -> tuple | None:
        """Retrieve and decrypt a credential by id.

        Returns (site, username, plain_password) or None when the id does not
        exist.
        """
        row = self._repo.get_by_id(entry_id)
        if row is None:
            return None
        return (row[0], row[1], decrypt_password(row[2]))
