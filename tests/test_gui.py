# pylint: disable=missing-function-docstring,unused-argument,redefined-outer-name,import-error,import-outside-toplevel,wrong-import-position,no-name-in-module,protected-access,use-implicit-booleaness-not-comparison,subprocess-run-check,too-few-public-methods,consider-using-from-import

"""GUI regression tests for tampered-vault handling (skipped without PyQt6).

Covers:
  * view/edit of a tampered entry crashing or silently showing an empty
    password instead of reporting a vault integrity error (MEDIUM)
  * malicious non-numeric ids in vault rows crashing row selection (LOW)
"""

import os

import pytest

pytest.importorskip("PyQt6.QtWidgets")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication  # noqa: E402

import main_gui  # noqa: E402
from app.database import connection  # noqa: E402
from app.database.connection import init_db  # noqa: E402
from app.database.repository import Repository  # noqa: E402
from app.services.password_service import PasswordService  # noqa: E402

TAMPERED_TOKEN = "gAAAAAcrippedciphertextAAAAAAAAAAAAAAAAAAAAAAAA"


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def widget(qapp, db_file, cipher):
    init_db()
    service = PasswordService(Repository())
    service.add("example-site.test", "alice", "correct-horse")
    w = main_gui.PasswordListWidget(service)
    yield w
    w.close()


def _tamper_vault() -> None:
    with connection.db() as conn:
        conn.execute("UPDATE passwords SET password = ?", (TAMPERED_TOKEN,))


def _capture(monkeypatch, name: str) -> list:
    calls = []
    monkeypatch.setattr(
        main_gui.QMessageBox, name, lambda *args, **kw: calls.append(args)
    )
    return calls


def test_view_tampered_entry_shows_integrity_warning(widget, monkeypatch):
    """Regression: tampering surfaced as an empty password in the dialog."""
    assert widget.table.rowCount() == 1
    widget.table.setCurrentCell(0, 0)
    _tamper_vault()
    warnings = _capture(monkeypatch, "warning")

    widget.view_password()  # must not raise

    assert len(warnings) == 1
    assert "Integrity" in str(warnings[0][1])


def test_edit_tampered_entry_shows_integrity_warning(widget, monkeypatch):
    widget.table.setCurrentCell(0, 0)
    _tamper_vault()
    warnings = _capture(monkeypatch, "warning")

    widget.edit_password()  # must not raise, must not open an editor

    assert len(warnings) == 1


def test_non_numeric_id_row_does_not_crash(widget, monkeypatch):
    """Regression: int(id_item.text()) raised ValueError on malicious rows.

    SQLite's INTEGER PRIMARY KEY rejects text ids, so the hostile case is a
    crafted schema (an untrusted vault.db may ship any schema at all).
    """
    with connection.db() as conn:
        conn.execute("DROP TABLE passwords")
        conn.execute(
            "CREATE TABLE passwords(id TEXT PRIMARY KEY, site TEXT,"
            " username TEXT, password TEXT,"
            " created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute(
            "INSERT INTO passwords(id, site, username, password)"
            " VALUES (?, ?, ?, ?)",
            ("evil-id", "evil\u202esite", "user\x1b[31m", "gAAAAAxxxx"),
        )
    widget.load_passwords()
    row = next(
        r
        for r in range(widget.table.rowCount())
        if widget.table.item(r, 0).text() == "evil-id"
    )
    # Bidi overrides and raw ANSI bytes are stripped from displayed cells.
    assert "\u202e" not in widget.table.item(row, 1).text()
    assert "\x1b" not in widget.table.item(row, 2).text()
    widget.table.setCurrentCell(row, 0)
    infos = _capture(monkeypatch, "information")

    assert widget.get_selected_id() is None
    widget.view_password()  # must not raise

    assert len(infos) == 1


def test_view_valid_entry_still_decrypts(widget, monkeypatch):
    """Functionality preserved: untampered entries open normally."""
    widget.table.setCurrentCell(0, 0)
    warnings = _capture(monkeypatch, "warning")
    infos = _capture(monkeypatch, "information")

    widget.view_password()

    assert warnings == []
    assert len(infos) == 1
    assert "correct-horse" in str(infos[0][2])
