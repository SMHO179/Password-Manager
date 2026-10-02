"""Shared helper utilities."""

import unicodedata

from rich.markup import escape


def strip_control_chars(value) -> str:
    """Remove characters that can escape or spoof terminal/table display.

    Drops C0/C1 control characters (raw ANSI/OSC escape sequences), Unicode
    format characters such as RTL overrides (bidi spoofing), and Unicode
    line/paragraph separators. Non-string input is coerced to text; None
    becomes an empty string.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return "".join(
        ch
        for ch in value
        if not (
            "\x00" <= ch < "\x20"
            or "\x7f" <= ch <= "\x9f"
            or unicodedata.category(ch) in {"Cf", "Zl", "Zp"}
        )
    )


def safe_display_text(value) -> str:
    """Make untrusted text safe to render in the terminal.

    Strips control/format characters (so raw ANSI/OSC escape sequences
    embedded in vault data can never reach the terminal, and Unicode
    overrides cannot spoof the displayed text) and escapes Rich markup
    (so stored text can neither inject styling/hyperlinks nor crash the
    renderer with malformed tags).
    """
    return escape(strip_control_chars(value))