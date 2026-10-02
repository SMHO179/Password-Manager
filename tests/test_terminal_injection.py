# pylint: disable=missing-function-docstring,unused-argument,redefined-outer-name,import-error,import-outside-toplevel,wrong-import-position,no-name-in-module,protected-access,use-implicit-booleaness-not-comparison,subprocess-run-check,too-few-public-methods,consider-using-from-import

"""Security regression tests for rendering untrusted vault data in the terminal.

Covers:
  * Rich markup injection via vault-controlled fields (hyperlink/styling
    injection, MarkupError crash of the list view) (LOW)
  * raw ANSI/OSC escape sequences from vault data reaching the terminal
    (LOW)
"""

from app.cli import menu

MALICIOUS_ROWS = [
    (1, "[bold]evil[/bold]", "user\x1b[31mRED", "2024-01-01 00:00:00"),
    (
        2,
        "bad [/] tag [notacolor]x",
        "bob\x1b]8;;http://evil.example\x07click",
        "2024-01-02 00:00:00",
    ),
    (3, "normal.example", "carol", "2024-01-03 00:00:00"),
]


class _StubService:
    def __init__(self, rows):
        self._rows = rows

    def list_all(self):
        return self._rows


def test_listing_malicious_vault_rows_does_not_crash(capsys, monkeypatch):
    """Regression: malformed markup raised MarkupError and aborted listing."""
    monkeypatch.setattr(menu, "pause", lambda: None)
    menu.list_passwords(_StubService(MALICIOUS_ROWS))
    out = capsys.readouterr().out
    # Markup is rendered literally instead of being interpreted or crashing
    # (normalise whitespace: narrow table columns wrap cell text).
    flat = " ".join(out.split())
    assert "[bold]evil[/bold]" in flat
    assert "bad [/] tag" in flat
    assert "[notacolor]x" in flat
    # Every injected token is present as literal text, not as markup.
    assert "[/bold]" in flat


def test_no_raw_escape_sequences_reach_the_terminal(capsys, monkeypatch):
    """Regression: ESC/OSC bytes were passed straight through to the TTY."""
    monkeypatch.setattr(menu, "pause", lambda: None)
    menu.list_passwords(_StubService(MALICIOUS_ROWS))
    out = capsys.readouterr().out
    assert "\x1b" not in out
    assert "\x07" not in out
    # The injected hyperlink target must never be emitted.
    assert "evil.example" not in out


def test_generated_password_markup_payload_does_not_crash(capsys, monkeypatch):
    """Regression: generated passwords draw from string.punctuation, so a
    password like 'x [/] y' could crash the CLI with MarkupError (or inject
    Rich styling) when interpolated unescaped into markup."""
    monkeypatch.setattr(
        menu, "generate_password", lambda length=16: "x [/] y [notacolor] z"
    )
    answers = iter(["16", "n", ""])
    monkeypatch.setattr(menu.Prompt, "ask", staticmethod(lambda *a, **k: next(answers)))

    menu.handle_generate_password()

    out = capsys.readouterr().out
    assert "x [/] y [notacolor] z" in out


def test_bidi_override_stripped_from_listing(capsys, monkeypatch):
    """Unicode RTL overrides in vault data must not reach the terminal
    (display spoofing)."""
    monkeypatch.setattr(menu, "pause", lambda: None)
    menu.list_passwords(
        _StubService([(4, "evil\u202esite.example", "bob\u202e", "2024-01-04 00:00:00")])
    )
    out = capsys.readouterr().out
    assert "\u202e" not in out
    assert "site.example" in " ".join(out.split())


def test_benign_rows_still_render(capsys, monkeypatch):
    monkeypatch.setattr(menu, "pause", lambda: None)
    menu.list_passwords(
        _StubService([(7, "github.com", "navab", "2024-01-01 00:00:00")])
    )
    out = capsys.readouterr().out
    assert "github.com" in out
    assert "navab" in out
    assert "7" in out
