"""SQL query constants."""

SQL_CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS passwords(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SQL_INSERT_PASSWORD = """\
INSERT INTO passwords(site, username, password)
VALUES (?, ?, ?)
"""

SQL_SELECT_PASSWORDS = """\
SELECT id, site, username, created_at
FROM passwords
ORDER BY id DESC
"""

SQL_SELECT_PASSWORD_BY_ID = """\
SELECT site, username, password FROM passwords WHERE id = ?
"""

SQL_DELETE_PASSWORD = "DELETE FROM passwords WHERE id = ?"

SQL_UPDATE_PASSWORD = """\
UPDATE passwords
SET site = ?, username = ?, password = ?
WHERE id = ?
"""
