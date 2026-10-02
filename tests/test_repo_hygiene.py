# pylint: disable=missing-function-docstring,unused-argument,redefined-outer-name,import-error,import-outside-toplevel,wrong-import-position,no-name-in-module,protected-access,use-implicit-booleaness-not-comparison,subprocess-run-check,too-few-public-methods,consider-using-from-import

"""Repository hygiene tests: no key/vault artifacts may live in git.

Covers:
  * secret.key / vault.db (and sidecars) being committed (CRITICAL in this
    project's history; prevented from recurring in the index)
  * .gitignore not covering vault/key artifacts (MEDIUM)
  * Fernet-key-shaped material embedded in tracked files (HIGH)
"""

import fnmatch
import subprocess
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]

# The test-suite itself contains intentionally fake tokens; skip it.
SCAN_EXCLUDE_PREFIX = ("tests/", ".venv/", ".git/")
SECRET_GLOBS = ("secret.key", "vault.db", "*.key", "*.db", "*.db-wal", "*.db-shm")
KEY_SHAPED = __import__("re").compile(
    rb"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{43}=[A-Za-z0-9_-]{1,2}(?![A-Za-z0-9_-])"
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _tracked_files() -> list[str]:
    return [line for line in _git("ls-files").splitlines() if line]


@pytest.mark.parametrize("glob", SECRET_GLOBS)
def test_no_secret_artifacts_tracked(glob: str):
    """Regression: secret.key and vault.db were committed to git."""
    offenders = [
        path for path in _tracked_files() if fnmatch.fnmatch(path, glob)
    ]
    # Plain 'vault.db' style names anywhere in the tree are equally unsafe.
    offenders += [
        path
        for path in _tracked_files()
        if Path(path).name == glob and glob not in ("*.key", "*.db", "*.db-wal", "*.db-shm")
    ]
    assert offenders == [], f"tracked secret artifacts: {sorted(set(offenders))}"


@pytest.mark.parametrize(
    "name",
    ["secret.key", "vault.db", "vault.db-wal", "vault.db-shm", "sub/other.db"],
)
def test_gitignore_covers_vault_artifacts(name: str):
    result = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "-q", name],
        capture_output=True,
    )
    assert result.returncode == 0, f"{name} is not covered by .gitignore"


def test_no_fernet_key_material_in_tracked_files():
    """A valid Fernet key embedded in any tracked text file fails the build."""
    offenders = []
    for path in _tracked_files():
        if path.startswith(SCAN_EXCLUDE_PREFIX):
            continue
        if (ROOT / path).exists():
            data = (ROOT / path).read_bytes()
        else:
            data = subprocess.run(
                ["git", "-C", str(ROOT), "show", f"HEAD:{path}"],
                capture_output=True,
                check=True,
            ).stdout
        if b"\x00" in data[:4096] or len(data) > 2_000_000:
            continue  # binary or large file
        for match in KEY_SHAPED.finditer(data):
            candidate = match.group(0)
            try:
                Fernet(candidate)
            except (ValueError, TypeError):
                continue
            offenders.append(f"{path}:{match.start()}")
    assert offenders == [], f"Fernet-key-shaped material tracked: {offenders}"


def test_index_matches_worktree_for_secret_files():
    """Files must not exist in the worktree without being tracked (or vice
    versa) for vault/key artifacts: both states are dangerous."""
    tracked = set(_tracked_files())
    for name in ("vault.db", "vault.db-wal", "vault.db-shm", "secret.key"):
        on_disk = (ROOT / name).exists()
        assert not on_disk, f"{name} exists in the working tree"
        assert name not in tracked, f"{name} is still tracked by git"
