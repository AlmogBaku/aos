"""`swap` and `discard` — the two ways a staged render leaves `rendered/.staging/<id>/`.

The gate between them is the installer's: it diffs the live render against the staged one
(`diff -ruN -x __pycache__ -x '*.pyc'`), and the user's approve runs `swap`, a decline runs
`discard`.
These verbs are the only code that moves a render, so the destructive half of a render
lives in tested code rather than in `mv`/`rm` lines four skills would each type by hand."""

import os
from pathlib import Path
from typing import Annotated

import typer

from ..constants import LOCK_REL
from ..errors import Exit, fail
from ..household import find_home
from ..lockfile import load_lock
from ..rendered import (
    check_id, live_dir, refuse_links, rendered_root, replaced_dir, staged_dir,
    staging_root, text_of, trash,
)

app = typer.Typer()


def _linked_targets(home: Path, live: Path) -> list[Path]:
    """Every recorded link target — any entry's own or used link — inside `live`. A staged
    tree must still hold each one, or the swap would leave those links dangling: a render
    that drops `adapters/` silently removes a permission gate at the next restart."""
    if not (home / LOCK_REL).is_file():
        return []
    out = []
    for entry in load_lock(home)["installs"].values():
        for target in {**(entry.get("links") or {}), **(entry.get("uses_links") or {})}.values():
            t = Path(target)
            if t == live or live in t.parents:
                out.append(t)
    return out


@app.command("swap", help="put a staged render live: rendered/.staging/<id> replaces "
                          "rendered/<id>, and the old render goes to the OS trash")
def cmd_swap(ctx: typer.Context,
             capability: Annotated[str, typer.Argument(help="capability id")]) -> None:
    home = find_home(ctx.obj)
    check_id(capability)
    root, staged = rendered_root(home), staged_dir(home, capability)
    live, aside = live_dir(home, capability), replaced_dir(home, capability)
    refuse_links(root, staging_root(home), staged, live, aside.parent, aside)
    if not staged.is_dir():
        fail(Exit.NOT_STAGED, f"nothing staged for '{capability}' at {staged}")

    # A crash between the two renames below leaves the old render aside. Beside a live
    # render it is a finished swap's leftover; with no live render it is the only copy.
    if aside.exists():
        if live.exists():
            trash(aside)
        else:
            os.rename(aside, live)
            fail(Exit.SWAP_RECOVERED,
                 f"an interrupted swap left the old render of '{capability}' aside; it is "
                 f"live again at {live} — run `aos-cap swap {capability}` again")

    # Bytecode is regenerated, never shipped: the gate hides it, so a staged .pyc would go
    # live unreviewed and run instead of the .py the user approved.
    cached = sorted(p for p in staged.rglob("*") if p.name == "__pycache__" or p.suffix == ".pyc")
    if cached:
        fail(Exit.STAGED_UNSAFE, f"{cached[0]} — a staged render must carry no bytecode "
                                 f"(the gate does not show it); re-render without it")
    needle = os.fspath(staged)
    for f in sorted(p for p in staged.rglob("*") if p.is_file() and not p.is_symlink()):
        text = text_of(f)
        if text is not None and needle in text:
            fail(Exit.STAGED_UNSAFE,
                 f"{f} names its own staging path ({needle}) — it would stop resolving once "
                 f"the render is live. Bake the live path, {live}, and re-render")
    for target in _linked_targets(home, live):
        if not (staged / target.relative_to(live)).exists():
            fail(Exit.STAGED_UNSAFE,
                 f"a recorded link targets {target}, which the staged render does not "
                 f"contain — swapping would leave that link dangling")

    aside.parent.mkdir(parents=True, exist_ok=True)
    first_install = not live.exists()
    if not first_install:
        os.rename(live, aside)
    try:
        os.rename(staged, live)
    except OSError as err:
        if aside.exists() and not live.exists():
            os.rename(aside, live)
        fail(Exit.GENERIC, f"could not move the staged render of '{capability}' live "
                           f"({err}); the old render is back in place")
    if aside.exists():
        trash(aside)
    print(f"swapped {capability}: {live}"
          + (" (first install)" if first_install else "; the old render is in the trash"))


@app.command("discard", help="decline a staged render: rendered/.staging/<id> goes to "
                             "the OS trash, the live render is untouched")
def cmd_discard(ctx: typer.Context,
                capability: Annotated[str, typer.Argument(help="capability id")]) -> None:
    home = find_home(ctx.obj)
    check_id(capability)
    staged = staged_dir(home, capability)
    refuse_links(rendered_root(home), staging_root(home), staged)
    if not staged.is_dir():
        fail(Exit.NOT_STAGED, f"nothing staged for '{capability}' at {staged}")
    trash(staged)
    print(f"discarded the staged render of {capability} (in the trash)")
