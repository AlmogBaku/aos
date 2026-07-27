"""The intake pipeline: `capture` writes into `.kb/pending/`, `pending` is the
generic queue view (add/list/resolve), `ingest` moves an item to `_raw/`, `inbox` is
the principal-scoped read view over the same directory. `find` joins them as the
read-side counterpart answering a metadata question over the same `kind`/`waits_on`
model."""

import hashlib
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from ..constants import PENDING_KINDS, WAITS_ON
from ..frontmatter import read_frontmatter, write_frontmatter
from ..query import parse_where, match_query, fm_get, WhereOpt, WithoutOpt
from ..identity import now_ts, today, die, git, resolve_principal
from ..base import Base, resolve_base, acting
from ._shared import acting_in

app = typer.Typer()
pending_app = typer.Typer(help="the one queue: add | list | resolve")
app.add_typer(pending_app, name="pending")


def _do_capture(base: Base, content: str, title: str, source: str, agent: str,
                author: tuple[str, str] | None = None, principal: str = "user",
                quiet: bool = False, corrects: str = ""):
    """Core capture: dedup + frontmatter + commit. Returns dest Path or None (dup)."""
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    # Dedup scans both halves: a capture waiting in .kb/pending/ and one already
    # ingested into _raw/ are the same fact, so either is a duplicate.
    for p in list(base.pending_dir.glob("*.md")) + list(base.raw_dir.rglob("*.md")):
        pfm, _ = read_frontmatter(p)
        if not pfm or pfm.get("source_sha256") != sha:
            continue
        if pfm.get("captured_by", "user") != principal:
            # Somebody else captured the same thing. Not our duplicate: dropping it
            # would silently discard this principal's write, and naming the file
            # would disclose a path that is not ours to show.
            continue
        if not quiet:
            print(f"duplicate: matches {base.rel(p)} — dropped.")
        return None
    # No triage: — location IS the state. In .kb/pending/ means pending; in _raw/ means
    # ingested and immutable.
    extra = {"type": "capture", "timestamp": today(), "source": source,
             "source_sha256": sha, "captured_at": now_ts(),
             "captured_by": principal, "verified": False}
    if corrects:
        extra["corrects"] = corrects
    dst = base.pending_add("capture", "agent", title,
                           content if content.endswith("\n") else content + "\n",
                           agent, extra)
    base.commit("capture", dst, f"pending: {title[:50]}", agent, author)
    return dst


@app.command("capture", help="instant mechanical capture into .kb/pending/")
def cmd_capture(
    ctx: typer.Context,
    text: Optional[str] = None,
    file: Optional[str] = None,
    title: Optional[str] = None,
    source: Annotated[Optional[str], typer.Option(
        help="channel provenance, e.g. whatsapp:voice")] = None,
    corrects: Annotated[Optional[str], typer.Option(
        help="path of the item this supersedes — a link, so the drain never has "
             "to LLM-match free text")] = None,
):
    base = resolve_base(ctx.obj)
    if file:
        content = Path(file).expanduser().read_text(encoding="utf-8")
        title = title or Path(file).stem
    elif text:
        content = text
        title = title or content.strip().splitlines()[0][:60]
    else:
        content = sys.stdin.read()
        title = title or (content.strip().splitlines() or ["capture"])[0][:60]
    if not content.strip():
        die("empty capture")
    corrects = (corrects or "").strip()
    if corrects and not (base.root / corrects).exists():
        # A path, not an id: lifecycle.md states "Identity is the file path (no slug
        # field)", so inventing an id here would contradict a standing doctrine.
        die(f"no such path to correct: {corrects}")
    agent, author, _ = acting(ctx.obj, base)
    # Scoped by the principal ID, not their grants subject: dedup and the queue are
    # per *person*, and two people can share one grant row (or hold none, falling
    # back to `user`) without becoming one identity.
    dst = _do_capture(base, content, title, source or "manual",
                      agent, author, author[1], corrects=corrects)
    if dst:
        print(f"captured: {base.rel(dst)} (pending, waits_on: agent)")


@app.command("find", help="metadata query over every page (`search` is the "
                          "full-text one — different question, both stay)")
def cmd_find(ctx: typer.Context, where: WhereOpt = [], without: WithoutOpt = []):
    """`kb find` answers a metadata question; `kb search` answers a full-text one.
    Both stay: they are different questions."""
    base = resolve_base(ctx.obj)
    where = parse_where(where)
    hits = 0
    for p in list(base.md_files(kinds=("wiki", "raw"))) + \
            sorted(base.pending_dir.glob("*.md")):
        fm, _ = read_frontmatter(p)
        if not fm or not match_query(fm, where, without):
            continue
        hits += 1
        fields = [f"{k}={fm_get(fm, k)}" for k, _, _ in where] or \
                 [f"type={fm.get('type', '?')}"]
        print(f"{base.rel(p)}  {' '.join(fields)}")
    print(f"({hits} match{'es' if hits != 1 else ''})")


@app.command("ingest", help="pending capture -> _raw/ (a git mv: location is the "
                            "state, and history has to follow)")
def cmd_ingest(ctx: typer.Context, path: Annotated[list[str], typer.Argument()]):
    """.kb/pending/ -> _raw/. Location is the state, so this move IS the state change.
    `git mv` rather than write-then-delete: `git log --follow` has to keep tracing the
    capture across it."""
    base, agent, author, _ = acting_in(ctx.obj)
    for rel in path:
        src = (base.root / rel).resolve()
        if not src.exists():
            die(f"no such pending item: {rel}")
        fm, body = read_frontmatter(src)
        if (fm or {}).get("kind") != "capture":
            die(f"{rel}: only kind: capture is ingested "
                f"(this is {(fm or {}).get('kind')!r})")
        base.raw_dir.mkdir(parents=True, exist_ok=True)
        dst = base.raw_dir / src.name
        n = 2
        while dst.exists():
            dst = base.raw_dir / f"{dst.stem}-{n}.md"
            n += 1
        git(base.root, "mv", base.rel(src), base.rel(dst))
        if src.exists():                     # not a repo, or mv declined
            src.rename(dst)
        # The queue's own fields go with the queue: they described where the item was
        # waiting, and it is not waiting any more.
        fm = {k: v for k, v in (fm or {}).items()
              if k not in ("kind", "waits_on", "raised_by")}
        write_frontmatter(dst, fm, body)
        # Both pathspecs: `git mv` stages the deletion and the addition together, but
        # `commit()` scopes its `git add`/`git commit --` to the paths it's given — a
        # dst-only commit leaves the pending file's deletion unstaged in the *commit*
        # even though the index already has it, so the source never actually leaves
        # the tree.
        base.commit("ingest", [rel, base.rel(dst)], f"ingested {src.name}",
                    agent, author)
        print(f"ingested: {base.rel(dst)}")


@pending_app.command("add")
def cmd_pending_add(
    ctx: typer.Context,
    kind: Annotated[str, typer.Option(help=str(sorted(PENDING_KINDS)))] = "finding",
    waits_on: Annotated[str, typer.Option(
        "--waits-on", help=str(sorted(WAITS_ON)))] = "human",
    title: str = "pending item",
    body: Annotated[Optional[str], typer.Option(help="short body inline")] = None,
    file: Annotated[Optional[str], typer.Option(
        help="body from a file, or - for stdin")] = None,
):
    """agents were hand-writing markdown into queue files, and --file is what makes a
    long body practical."""
    # Argparse's choices= validated --kind/--waits-on before the subcommand body ever
    # ran, so a bad value was always the reported error even with no resolvable base.
    # PENDING_KINDS/WAITS_ON are runtime sets, not literals, so they can't become a
    # static Literal[...] the way audience/sync/curation did — checked by hand here,
    # deliberately BEFORE resolve_base(), to keep that ordering.
    if kind not in PENDING_KINDS:
        die(f"unknown --kind {kind!r} — the closed set is "
            f"{' '.join(sorted(PENDING_KINDS))}")
    if waits_on not in WAITS_ON:
        die(f"unknown --waits-on {waits_on!r} — the closed set is "
            f"{' '.join(sorted(WAITS_ON))}")
    base = resolve_base(ctx.obj)
    agent, author, _ = acting(ctx.obj, base)
    if file == "-":
        body = sys.stdin.read()
    elif file:
        body = Path(file).expanduser().read_text(encoding="utf-8")
    else:
        body = body or ""
    if not body.strip():
        die("empty pending entry — pass --body, --file <path>, or --file - "
            "for stdin")
    entry = base.pending_add(kind, waits_on, title, body, agent)
    base.commit("pending", entry, f"{kind} pending: {title[:50]}", agent, author)
    print(f"pending: {base.rel(entry)}")


@pending_app.command("list")
def cmd_pending_list(ctx: typer.Context, where: WhereOpt = [], without: WithoutOpt = []):
    """The queue is a view over a directory."""
    base = resolve_base(ctx.obj)
    where = parse_where(where)
    hits = 0
    for p in sorted(base.pending_dir.glob("*.md")):
        fm, _ = read_frontmatter(p)
        if not fm or not match_query(fm, where, without):
            continue
        hits += 1
        flag = f"  FAILED: {fm['failed']}" if fm.get("failed") else ""
        print(f"{base.rel(p)}  {fm.get('kind', '?')}/"
              f"{fm.get('waits_on', '?')}  {fm.get('title', '')}{flag}")
    print(f"({hits} pending item{'s' if hits != 1 else ''})")


@pending_app.command("resolve")
def cmd_pending_resolve(ctx: typer.Context,
                        path: Annotated[list[str], typer.Argument()] = []):
    base, agent, author, _ = acting_in(ctx.obj)
    for rel in path:
        p = base.root / rel
        if not p.exists():
            die(f"no such pending item: {rel}")
        if git(base.root, "rm", "-q", "--", base.rel(p)).returncode != 0:
            p.unlink()
        base.commit("resolve", [rel], f"resolved {Path(rel).name}", agent, author)
        print(f"resolved: {rel}")


@app.command("inbox", help="the inbox is a view: this principal's pending items "
                          "(--all for everyone's)")
def cmd_inbox(
    ctx: typer.Context,
    failed: bool = False,
    all: Annotated[bool, typer.Option(
        help="include other principals' items (designated-curator and CI path); "
             "default is yours alone")] = False,
    where: WhereOpt = [],
    without: WithoutOpt = [],
):
    """The inbox is a view, and by default it is *this principal's* view.

    A base several people share otherwise hands every household's archiver every
    other household's pending captures: the same captures get promoted once per
    household, and one person's raw material lands in another person's agent context
    while that agent holds write access to shared knowledge. `--all` is the
    designated-curator (and CI) path."""
    base = resolve_base(ctx.obj)
    # Read-only, so it resolves without establishing: see resolve_principal's `persist`.
    principal = resolve_principal(ctx.obj, base.cfg.get("name", base.root.name),
                                 base.root, persist=False)
    where = parse_where(where)
    # The designated curator's whole job is reading everyone's raw material, so it needs
    # no flag. `--all` survives for the CI path, but it stops being silent about it.
    curating = base.is_curator(principal)
    show_all = curating or all
    if all and not curating:
        print("note: `--all` — showing other principals' pending items on an "
              f"audience: {base.audience()} base under curation: {base.curation()}. "
              "That is somebody else's raw material.", file=sys.stderr)
    found = others = 0
    for p in sorted(base.pending_dir.glob("*.md")):
        fm, _ = read_frontmatter(p)
        if not fm or fm.get("waits_on") != "agent":
            continue
        # --failed narrows to items that errored; they stay in the queue, because an
        # error is not a change of location.
        if bool(fm.get("failed")) != bool(failed):
            continue
        if not match_query(fm, where, without):
            continue
        if not show_all and fm.get("captured_by", "user") != principal:
            others += 1
            continue
        found += 1
        extra = f"  error: {fm['failed']}" if fm.get("failed") else ""
        print(f"{base.rel(p)}  [{fm.get('captured_at', '?')}]{extra}")
    want = "failed" if failed else "pending"
    print(f"({found} {want} item{'s' if found != 1 else ''})")
    if others:
        # A count, never a path: the point is to say the queue is not empty for
        # someone else, not to show what they captured.
        print(f"({others} more belong to other principals — `--all` to include)")
