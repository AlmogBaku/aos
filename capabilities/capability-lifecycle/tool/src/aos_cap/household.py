"""Finding the household root — the `<home>/` that holds `.aos/`, `upstream/` and
`personal/`. Two flavours, because two kinds of caller need it: a verb that cannot
work without one (exit 15), and the collision gate, which degrades to "no household
resolved" and says so in its report."""

import os
from pathlib import Path
from typing import Optional, Protocol

from .errors import Exit, fail


class HasHome(Protocol):
    """What both finders read off the options object: the raw `--home` string, or None.
    `GlobalOpts` (commands/_shared.py) satisfies this structurally, which is why the
    attribute is named `home` there and here."""
    home: Optional[str]


def find_home(opts: HasHome, require_existing: bool = True) -> Path:
    if opts.home:
        root = Path(opts.home).expanduser()
    elif os.environ.get("AOS_HOME"):
        root = Path(os.environ["AOS_HOME"]).expanduser()
    elif not require_existing:
        fail(Exit.NO_HOME,
             "init creates state — name the household explicitly (--home or AOS_HOME)")
    else:
        cur = Path.cwd()
        for cand in [cur, *cur.parents]:
            if (cand / ".aos").is_dir():
                return cand
        fail(Exit.NO_HOME, "no household found: no .aos/ directory from cwd upward "
                           "(pass --home or set AOS_HOME)")
    if require_existing and not (root / ".aos").is_dir():
        fail(Exit.NO_HOME, f"no .aos/ directory under {root}")
    return root


def find_home_soft(opts: HasHome, cap_dir: Optional[Path] = None) -> Optional[Path]:
    """The household if one is resolvable, else None.

    Discovery walks up from the CAPABILITY DIRECTORY as well as the cwd, because that is
    the one path every caller supplies: a capability lives at
    `<home>/{upstream,personal}/capabilities/<id>`, while the agent's cwd is wherever the
    harness put it. Relying on cwd alone made `--check` skip the household and lockfile
    sources on a real machine and still report "clean" — a silent no-op in the gate."""
    if opts.home:
        root = Path(opts.home).expanduser()
        if not (root / ".aos").is_dir():
            fail(Exit.NO_HOME, f"no .aos/ directory under {root}")
        return root
    if os.environ.get("AOS_HOME"):
        root = Path(os.environ["AOS_HOME"]).expanduser()
        if (root / ".aos").is_dir():
            return root
    starts = ([Path(cap_dir).resolve()] if cap_dir else []) + [Path.cwd()]
    for start in starts:
        for cand in [start, *start.parents]:
            if (cand / ".aos").is_dir():
                return cand
    return None
