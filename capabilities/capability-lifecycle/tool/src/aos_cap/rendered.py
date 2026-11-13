"""The rendered tree: where every installed capability's render lives.

`<aos_home>/rendered/<id>/` is the live render of capability `<id>` — shipped or the user's
own — and every harness link points into it. It is unversioned and machine-local: a render
is build output (source + version + the user's MOD), so it is not kept in `personal/`, the
user's source repo. Two siblings hold renders in flight:

  rendered/.staging/<id>/    the ONLY place a render is written; the gate diffs it
  rendered/.replaced/<id>/   the live render, held aside for the length of one swap

Nothing here is ever `rmtree`d: a render that leaves goes to the OS trash (`send2trash`),
so a regretted upgrade is recoverable from there."""

import os
from pathlib import Path

from .constants import SKILL_NAME_MAX, SKILL_NAME_RE
from .errors import Exit, fail

RENDERED = "rendered"
STAGING = ".staging"
REPLACED = ".replaced"


def rendered_root(home: Path) -> Path:
    return home / RENDERED


def staging_root(home: Path) -> Path:
    return home / RENDERED / STAGING


def live_dir(home: Path, cap: str) -> Path:
    return home / RENDERED / cap


def staged_dir(home: Path, cap: str) -> Path:
    return home / RENDERED / STAGING / cap


def replaced_dir(home: Path, cap: str) -> Path:
    return home / RENDERED / REPLACED / cap


def check_id(cap: str) -> None:
    """A capability id is one path segment of the kit's name grammar. Checked by grammar,
    not by where the path lands: `..` resolves to `rendered/` itself, which is inside the
    tree and would read as "contained", and `.staging` is a sibling of every render."""
    if not cap or len(cap) > SKILL_NAME_MAX or not SKILL_NAME_RE.match(cap):
        fail(Exit.BAD_RENDER_ID,
             f"'{cap}' is not a capability id (lowercase letters, digits, single hyphens)")


def refuse_links(*paths: Path) -> None:
    """Every directory a swap or discard moves must be a real directory: a symlinked
    `.staging/<id>` would move (or trash) whatever it points at."""
    for p in paths:
        if p.is_symlink():
            fail(Exit.BAD_RENDER_ID, f"{p} is a symlink — renders are real directories")


def is_under(path: Path, root: Path) -> bool:
    """`path` is `root` or inside it, compared on resolved paths (symlinks followed)."""
    p, r = path.resolve(), root.resolve()
    return p == r or r in p.parents


def trash(path: Path) -> None:
    from send2trash import send2trash
    send2trash(os.fspath(path))


def text_of(path: Path):
    """The file's text, or None for anything that is not UTF-8 text: bytecode, images,
    archives. Only text is ever searched or rewritten — a byte-level substitution of a path
    prefix inside a `.pyc` corrupts it without changing its size or mtime, so the import
    that trusts the cache then fails, and a gate plugin that fails to import is simply off."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None
