"""The lockfile as data: load/save, the hash and symlink primitives every entry is made
of, and the one lookup (`get_entry`) that turns a capability name into its entry or
exit 14. This file is THIS TOOL'S — agents call verbs, never edit the YAML — so it is
rewritten wholesale on every write rather than patched.

The verbs that use all of this live in commands/lockfile.py."""

import hashlib
import os
from pathlib import Path
from typing import Union

import yaml

from .constants import LOCK_REL
from .errors import Exit, fail


def load_lock(root: Path) -> dict:
    path = root / LOCK_REL
    if not path.is_file():
        fail(Exit.NO_HOME, f"no lockfile at {path} (run: aos-cap init)")
    data = yaml.safe_load(path.read_text()) or {}
    data.setdefault("version", 1)
    data.setdefault("installs", {})
    return data


def save_lock(root: Path, data: dict) -> None:
    (root / LOCK_REL).write_text(yaml.safe_dump(data, sort_keys=True))


def sha256(path: Union[str, Path]) -> str:
    p = Path(path)
    if not p.is_file():
        fail(Exit.ARTIFACT_MISSING, f"artifact not found: {path}")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def readlink_or_fail(path: Union[str, Path]) -> str:
    p = Path(path).expanduser()
    if not p.is_symlink():
        fail(Exit.ARTIFACT_MISSING, f"not a symlink: {path}")
    return link_target(p)


def artifact_path(arg: Union[str, Path]) -> Path:
    """Artifacts are files; symlinks belong in --link (they are verified structurally,
    and hashing through one would silently record the target's identity instead)."""
    p = Path(arg).expanduser()
    if p.is_symlink():
        fail(Exit.ARTIFACT_MISSING, f"symlink passed as --artifact (use --link): {arg}")
    return p.resolve()


def link_target(p: Path) -> str:
    """Absolute + lexically normalized, identically for relative and absolute links, so
    the two spellings of one destination compare equal. Deliberately NOT resolve(): a
    household under a symlinked path must not read as drift."""
    target = os.readlink(p)
    if not os.path.isabs(target):
        target = os.path.join(str(Path(p).parent.absolute()), target)
    return os.path.normpath(target)


def get_entry(root: Path, capability: str) -> tuple[dict, dict]:
    lock = load_lock(root)
    if capability not in lock["installs"]:
        fail(Exit.NO_ENTRY, f"no lockfile entry for '{capability}'")
    return lock, lock["installs"][capability]
