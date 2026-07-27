"""Thin, mostly-independent, cross-cutting verbs: `config` (get/set), `grants` (a
pure lookup, no writes), `commit` (the escape hatch for hand-written changes),
`history` (read-only git log formatting), `refuse` (records a refusal). None share
enough mechanism with each other or with lifecycle/capture/wiki to earn their own
module."""

import sys
from typing import Annotated, Literal, Optional

import typer
import yaml

from ..constants import AOS_VERBS
from ..identity import die, is_repo, git, load_principals, save_principals, \
    principal_file
from ..base import resolve_base, acting

app = typer.Typer()


@app.command("grants", help="grant lookup")
def cmd_grants(ctx: typer.Context,
              check: Annotated[Literal["check"], typer.Argument()],
              subject: Annotated[str, typer.Option()],
              verb: Annotated[str, typer.Option()],
              path: Annotated[str, typer.Option()]):
    base = resolve_base(ctx.obj)
    ok = base.grant_check(subject, verb, path)
    print(f"{'GRANTED' if ok else 'DENIED'}: {subject} {verb} {path}")
    sys.exit(0 if ok else 1)


@app.command("config", help="get/set base config; principal.* is machine-local")
def cmd_config(ctx: typer.Context, op: Literal["get", "set"],
               assignment: Annotated[str, typer.Argument(metavar="key[=value]")]):
    """get/set, with principal.* routed to the machine-local file and everything else to
    .kb/base.yml. This is what replaces the init step: the tool establishes itself on
    first use, and config is how you correct it afterwards."""
    if op == "set" and "=" not in assignment:
        die("config set takes key=value")
    key, _, value = assignment.partition("=")
    key, value = key.strip(), value.strip()
    base = None if key.startswith("principal.") else resolve_base(ctx.obj)

    if key.startswith("principal."):
        field = key.split(".", 1)[1]
        if field != "id":
            die(f"principal.{field} is not settable — the file holds ids and their "
                f"base globs; edit {principal_file()} for anything richer")
        entries = load_principals()
        if op == "get":
            print(entries[0]["id"] if entries else "(none)")
            return
        save_principals([{"id": value, "bases": ["*"]}]
                        + [e for e in entries
                           if isinstance(e, dict) and e.get("id") != value])
        print(f"principal.id = {value}  ({principal_file()})")
        return

    cfg_path = base.kb_dir / "base.yml"
    parts = key.split(".")
    if op == "get":
        cur = base.cfg
        for part in parts:
            if not isinstance(cur, dict) or part not in cur:
                die(f"{key}: not set in {base.rel(cfg_path)}")
            cur = cur[part]
        print(cur if not isinstance(cur, (dict, list))
              else yaml.safe_dump(cur, sort_keys=False).strip())
        return

    agent, author, _ = acting(ctx.obj, base)
    cur = base.cfg
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
        if not isinstance(cur, dict):
            die(f"{key}: {part} is not a mapping")
    cur[parts[-1]] = yaml.safe_load(value)
    # Rewritten wholesale: the file is the tool's own, and a surgical edit that
    # preserved comments would have to parse YAML twice and could disagree with itself.
    cfg_path.write_text(yaml.safe_dump(base.cfg, sort_keys=False,
                                       allow_unicode=True), encoding="utf-8")
    base.commit("config", [base.rel(cfg_path)], f"{key} = {value}", agent, author)
    print(f"{key} = {value}  ({base.rel(cfg_path)})")


@app.command("refuse", help="record a refused write (refuse commit + review-queue "
                           "entry); payload stays with the caller")
def cmd_refuse(ctx: typer.Context, path: Annotated[str, typer.Option()],
               verb: str = "write", subject: Optional[str] = None,
               reason: Optional[str] = None):
    """Record a refused write: a `refuse` commit plus a pending entry ([D] per
    kb-authorization §3.1). The payload stays with the caller — this only records.
    A refusal is one of the events git could not otherwise hold, since by definition
    nothing else changed; the queue entry is what gives it a file to commit."""
    base = resolve_base(ctx.obj)
    agent, author, _ = acting(ctx.obj, base)
    entry = base.pending_add(
        "refusal", "human", f"refused write — {path}",
        f"Subject `{subject or agent}` was refused `{verb}` on "
        f"`{path}`: {reason or 'no grant'}. The payload stays with the "
        f"caller; install the capability properly (grants via the diff gate) or "
        f"dismiss.", agent)
    base.commit("refuse", entry, (reason or "no grant")[:120], agent, author)
    print(f"refusal recorded: {path}")


@app.command("commit", help="attribute a hand-written change (author = principal, "
                           "committer = agent, aos-verb trailer)")
def cmd_commit(
    ctx: typer.Context,
    verb: Annotated[str, typer.Option(help="one of the aos-verb vocabulary")],
    path: Annotated[list[str], typer.Option(help="repeatable; base-relative")],
    summary: Annotated[str, typer.Option()],
):
    """Attribute a hand-written change.

    Wiki pages are written with an agent's own file tools, not by a verb here, so
    without this they would reach git only through sync's unattributed sweep. This is
    the swap for the log line an agent used to append by hand — same closed
    vocabulary, carried by the commit that actually made the change."""
    base = resolve_base(ctx.obj)
    if verb not in AOS_VERBS:
        die(f"unknown aos-verb {verb!r} — one of {', '.join(sorted(AOS_VERBS))}")
    missing = [p for p in path if not (base.root / p).exists()]
    if missing:
        die(f"no such path in the base: {', '.join(missing)}")
    agent, author, _ = acting(ctx.obj, base)
    if not base.commit(verb, path, summary, agent, author):
        die("nothing to commit — those paths are unchanged", 1)
    print(f"committed: {verb} — {', '.join(path)}")


@app.command("history", help="recent activity from git — the orientation read, in "
                            "a pinned format")
def cmd_history(ctx: typer.Context, limit: int = 30):
    """Recent activity — the orientation read log.md used to serve. Git already holds
    it; this only pins the format so it stays as parseable as the old grammar was."""
    base = resolve_base(ctx.obj)
    if not is_repo(base.root):
        die("not a git repo — no history")
    fmt = ("%cI%x1f%an%x1f%cn%x1f%s%x1f"
           "%(trailers:key=aos-path,valueonly,separator=%x2C)")
    out = git(base.root, "log", f"-{limit}", f"--pretty={fmt}").stdout
    rows = 0
    for line in out.splitlines():
        parts = line.split("\x1f")
        if len(parts) < 5:
            continue
        when, author, committer, subject, paths = parts[:5]
        rows += 1
        print(f"{when} | {author} | {committer} | {subject} | "
              f"{paths.strip() or '—'}")
    if not rows:
        print("(no history yet)")
