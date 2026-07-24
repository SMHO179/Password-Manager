"""Password strength evaluation utilities."""

import string


def _calculate_score(password: str) -> int:
    """Calculate a password strength score (0-6)."""
    score = 0
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1
    return score


def check_password_strength(password: str) -> tuple[str, str]:
    """Return a (label, colour) pair describing password strength.

    Intended for the CLI front-end.
    """
    score = _calculate_score(password)
    if score <= 2:
        return "Weak", "red"
    if score <= 4:
        return "Medium", "yellow"
    if score == 5:
        return "Strong", "green"
    return "Very Strong", "bright_green"


_STRENGTH_STYLE_MAP = {
    "red": "strengthWeak",
    "yellow": "strengthMedium",
    "green": "strengthStrong",
    "bright_green": "strengthVeryStrong",
}


def check_password_strength_gui(password: str) -> tuple[str, str, str]:
    """Return a (label, colour, stylesheet_id) describing password strength.

    Intended for the GUI front-end which needs a Qt stylesheet object name.
    """
    label, colour = check_password_strength(password)
    return label, colour, _STRENGTH_STYLE_MAP[colour]
