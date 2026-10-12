"""Finding the household root — the `<home>/` that holds `.aos/`, `upstream/` and
`personal/`: `--home`, else `$AOS_HOME`, else `~/aos`. Named, never discovered — a
cwd-upward search for `.aos/` let any folder carrying one become the household. Two
flavours, because two kinds of caller need it: a verb that cannot work without one
(exit 15), and the collision gate, which degrades to "no household resolved" and says
so in its report."""

import os
from pathlib import Path
from typing import Optional, Protocol

from .errors import Exit, fail


class HasHome(Protocol):
    """What both finders read off the options object: the raw `--home` string, or None.
    `GlobalOpts` (commands/_shared.py) satisfies this structurally, which is why the
    attribute is named `home` there and here."""
    home: Optional[str]


def _explicit_home(opts: HasHome) -> Optional[Path]:
    if opts.home:
        return Path(opts.home).expanduser()
    if os.environ.get("AOS_HOME"):
        return Path(os.environ["AOS_HOME"]).expanduser()
    return None


def find_home(opts: HasHome, require_existing: bool = True) -> Path:
    root = _explicit_home(opts)
    if root is None:
        if not require_existing:
            fail(Exit.NO_HOME,
                 "init creates state — name the household explicitly (--home or AOS_HOME)")
        root = Path.home() / "aos"
        if not (root / ".aos").is_dir():
            fail(Exit.NO_HOME, f"no .aos/ directory under {root}, the default home "
                               f"(pass --home or set AOS_HOME)")
    if require_existing and not (root / ".aos").is_dir():
        fail(Exit.NO_HOME, f"no .aos/ directory under {root}")
    return root


def find_home_soft(opts: HasHome) -> Optional[Path]:
    """The household if one resolves, else None — `find_home`'s resolution with one
    difference: the `~/aos` default without a `.aos/` is "no household", not exit 15.
    An explicit home (`--home`/`$AOS_HOME`) without one still exits 15: falling through
    to look elsewhere would let the gate report "clean" against a household nobody
    named."""
    root = _explicit_home(opts)
    if root is not None:
        if not (root / ".aos").is_dir():
            fail(Exit.NO_HOME, f"no .aos/ directory under {root}")
        return root
    root = Path.home() / "aos"
    return root if (root / ".aos").is_dir() else None
