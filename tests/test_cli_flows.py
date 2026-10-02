# pylint: disable=missing-function-docstring,unused-argument,redefined-outer-name,import-error,import-outside-toplevel,wrong-import-position,no-name-in-module,protected-access,use-implicit-booleaness-not-comparison,subprocess-run-check,too-few-public-methods,consider-using-from-import

"""CLI flow tests: input handling and information-leak checks.

Covers:
  * add_password() crashing (TypeError) when the user cancels at the
    password prompt with 'b' (LOW, availability)
  * echoed output must never contain the entered password (info leak)
  * generated passwords still work end to end (functionality preserved)
"""

from app.cli import menu
from app.services.password_generator import generate_password


class _RecordingService:
    def __init__(self):
        self.added = []

    def add(self, site, username, password):
        self.added.append((site, username, password))


def _scripted_prompts(monkeypatch, answers):
    """Replace prompt_or_back with scripted answers, mirroring its real
    semantics: the user typing 'b' yields None (go back)."""
    iterator = iter(answers)

    def _prompt(*args, **kwargs):
        value = next(iterator)
        return None if value.lower() == "b" else value

    monkeypatch.setattr(menu, "prompt_or_back", _prompt)


def test_add_password_cancelled_at_password_prompt_does_not_crash(
    monkeypatch, capsys
):
    """Regression: check_password_strength(None) raised TypeError."""
    _scripted_prompts(monkeypatch, ["example.com", "alice", "b"])
    service = _RecordingService()

    menu.add_password(service)

    assert service.added == []
    capsys.readouterr()


def test_add_password_saves_and_does_not_echo_secret(monkeypatch, capsys):
    _scripted_prompts(monkeypatch, ["example.com", "alice", "s3cret-value"])
    monkeypatch.setattr(menu, "pause", lambda: None)
    service = _RecordingService()

    menu.add_password(service)

    assert service.added == [("example.com", "alice", "s3cret-value")]
    out = capsys.readouterr().out
    assert "s3cret-value" not in out


def test_add_password_cancelled_at_site_prompt(monkeypatch):
    _scripted_prompts(monkeypatch, ["b"])
    service = _RecordingService()
    menu.add_password(service)
    assert service.added == []


def test_generated_password_length_and_alphabet():
    for length in (4, 16, 64):
        password = generate_password(length)
        assert len(password) == length
        assert all(
            c.isalnum() or c in "!@#$%^&*()-_=+[]{};:'\",.<>/?\\|`~"
            for c in password
        )


def test_generator_rejects_tiny_lengths():
    # Lengths below the floor are clamped up instead of raising or looping.
    assert len(generate_password(1)) == 4
    assert len(generate_password(0)) == 4
    assert len(generate_password(-5)) == 4
