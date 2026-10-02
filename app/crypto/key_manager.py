"""Encryption key file management.

The key file is the root of trust for the vault, so every access is
hardened: creation is atomic and exclusive with mode 0600, symlinks and
non-regular files are refused, and the content is validated before use.
"""

import os
import stat

from cryptography.fernet import Fernet

from app.config import KEY_FILE

_KEY_MODE = stat.S_IRUSR | stat.S_IWUSR  # 0600, owner read/write only


class KeyFileError(Exception):
    """Raised when the key file is missing, unsafe, or malformed."""


def _open_flags(*, create: bool) -> int:
    """Build open(2) flags that refuse symlinks and close-on-exec."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL if create else os.O_RDONLY
    for name in ("O_NOFOLLOW", "O_CLOEXEC", "O_NONBLOCK"):
        flags |= getattr(os, name, 0)
    return flags


def _restrict(fd: int) -> None:
    """Force owner-only permissions on an open file descriptor."""
    if hasattr(os, "fchmod"):
        os.fchmod(fd, _KEY_MODE)
    else:  # pragma: no cover - platforms without fchmod (e.g. Windows)
        os.chmod(KEY_FILE, _KEY_MODE)


def _read_key_file() -> bytes:
    """Read and validate the key file without ever following a symlink."""
    try:
        fd = os.open(KEY_FILE, _open_flags(create=False))
    except OSError as exc:
        raise KeyFileError(
            f"cannot open key file {KEY_FILE}: {exc.strerror or exc}"
        ) from exc
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise KeyFileError(
                f"key file {KEY_FILE} is not a regular file; refusing to use it"
            )
        # A Fernet key is 44 bytes; reading more than enough to spot garbage.
        key = os.read(fd, 512)
        # Restrict permissions on the exact inode that was just read so a
        # swapped-in file cannot leave a world-readable key behind.
        _restrict(fd)
    except OSError as exc:
        raise KeyFileError(
            f"cannot secure key file {KEY_FILE}: {exc.strerror or exc}"
        ) from exc
    finally:
        os.close(fd)

    key = key.strip()
    try:
        Fernet(key)
    except (ValueError, TypeError) as exc:
        raise KeyFileError(
            f"key file {KEY_FILE} does not contain a valid encryption key"
        ) from exc
    return key


def _create_key_file() -> bytes:
    """Atomically create the key file with owner-only permissions.

    Raises ``FileExistsError`` when something already occupies the path so
    callers can decide between loading it (never overwriting a key) and
    failing (refusing to clobber one).
    """
    key = Fernet.generate_key()
    try:
        fd = os.open(KEY_FILE, _open_flags(create=True), _KEY_MODE)
    except FileExistsError:
        raise
    except OSError as exc:
        raise KeyFileError(
            f"cannot create key file {KEY_FILE}: {exc.strerror or exc}"
        ) from exc
    try:
        _restrict(fd)  # defeat a permissive umask
        os.write(fd, key)
        os.fsync(fd)
    except OSError as exc:
        try:
            os.unlink(KEY_FILE)  # never leave a partially written key behind
        except OSError:
            pass
        raise KeyFileError(
            f"cannot write key file {KEY_FILE}: {exc.strerror or exc}"
        ) from exc
    finally:
        os.close(fd)
    return key


def load_or_create_key() -> bytes:
    """Load the existing key file or atomically generate a new one."""
    if os.path.lexists(KEY_FILE):
        return _read_key_file()
    try:
        return _create_key_file()
    except FileExistsError:
        # Another process created the file between the check and the write.
        return _read_key_file()


def generate_key_file() -> None:
    """Generate a new encryption key and write it to disk.

    Refuses to overwrite anything that already occupies the key path.
    """
    if os.path.lexists(KEY_FILE):
        raise KeyFileError(f"key file {KEY_FILE} already exists; refusing to overwrite")
    try:
        _create_key_file()
    except FileExistsError as exc:
        raise KeyFileError(
            f"key file {KEY_FILE} appeared while generating; refusing to overwrite"
        ) from exc
