"""Password strength evaluation utilities."""

import string


def _calculate_score(password: str) -> int:
    """Calculate a password strength score (0-6)."""
    score = 0
    length = len(password)
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1

    has_lower = False
    has_upper = False
    has_digit = False
    has_punct = False
    for c in password:
        if not has_lower and c.islower():
            has_lower = True
        elif not has_upper and c.isupper():
            has_upper = True
        elif not has_digit and c.isdigit():
            has_digit = True
        elif not has_punct and c in string.punctuation:
            has_punct = True
        if has_lower and has_upper and has_digit and has_punct:
            break

    if has_lower:
        score += 1
    if has_upper:
        score += 1
    if has_digit:
        score += 1
    if has_punct:
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
