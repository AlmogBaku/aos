"""Thin, mostly-independent, cross-cutting verbs: `config` (get/set), `grants` (a
pure lookup, no writes), `commit` (the escape hatch for hand-written changes),
`history` (read-only git log formatting), `refuse` (records a refusal). None share
enough mechanism with each other or with lifecycle/capture/wiki to earn their own
module."""

import sys

import yaml

from ..constants import AOS_VERBS
from ..identity import die, is_repo, git, load_principals, save_principals, \
    principal_file
from ..base import resolve_base, acting


def cmd_grants(args):
    base = resolve_base(args)
    ok = base.grant_check(args.subject, args.verb, args.path)
    print(f"{'GRANTED' if ok else 'DENIED'}: {args.subject} {args.verb} {args.path}")
    sys.exit(0 if ok else 1)


def cmd_config(args):
    """get/set, with principal.* routed to the machine-local file and everything else to
    .kb/base.yml. This is what replaces the init step: the tool establishes itself on
    first use, and config is how you correct it afterwards."""
    if args.op == "set" and "=" not in args.assignment:
        die("config set takes key=value")
    args.key, _, args.value = args.assignment.partition("=")
    args.key = args.key.strip()
    args.value = args.value.strip()
    base = None if args.key.startswith("principal.") else resolve_base(args)

    if args.key.startswith("principal."):
        field = args.key.split(".", 1)[1]
        if field != "id":
            die(f"principal.{field} is not settable — the file holds ids and their "
                f"base globs; edit {principal_file()} for anything richer")
        entries = load_principals()
        if args.op == "get":
            print(entries[0]["id"] if entries else "(none)")
            return
        save_principals([{"id": args.value, "bases": ["*"]}]
                        + [e for e in entries
                           if isinstance(e, dict) and e.get("id") != args.value])
        print(f"principal.id = {args.value}  ({principal_file()})")
        return

    cfg_path = base.kb_dir / "base.yml"
    parts = args.key.split(".")
    if args.op == "get":
        cur = base.cfg
        for part in parts:
            if not isinstance(cur, dict) or part not in cur:
                die(f"{args.key}: not set in {base.rel(cfg_path)}")
            cur = cur[part]
        print(cur if not isinstance(cur, (dict, list))
              else yaml.safe_dump(cur, sort_keys=False).strip())
        return

    agent, author, _ = acting(args, base)
    cur = base.cfg
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
        if not isinstance(cur, dict):
            die(f"{args.key}: {part} is not a mapping")
    cur[parts[-1]] = yaml.safe_load(args.value)
    # Rewritten wholesale: the file is the tool's own, and a surgical edit that
    # preserved comments would have to parse YAML twice and could disagree with itself.
    cfg_path.write_text(yaml.safe_dump(base.cfg, sort_keys=False,
                                       allow_unicode=True), encoding="utf-8")
    base.commit("config", [base.rel(cfg_path)], f"{args.key} = {args.value}",
                agent, author)
    print(f"{args.key} = {args.value}  ({base.rel(cfg_path)})")


def cmd_refuse(args):
    """Record a refused write: a `refuse` commit plus a pending entry ([D] per
    kb-authorization §3.1). The payload stays with the caller — this only records.
    A refusal is one of the events git could not otherwise hold, since by definition
    nothing else changed; the queue entry is what gives it a file to commit."""
    base = resolve_base(args)
    agent, author, _ = acting(args, base)
    entry = base.pending_add(
        "refusal", "human", f"refused write — {args.path}",
        f"Subject `{args.subject or agent}` was refused `{args.verb}` on "
        f"`{args.path}`: {args.reason or 'no grant'}. The payload stays with the "
        f"caller; install the capability properly (grants via the diff gate) or "
        f"dismiss.", agent)
    base.commit("refuse", entry, (args.reason or "no grant")[:120], agent, author)
    print(f"refusal recorded: {args.path}")


def cmd_commit(args):
    """Attribute a hand-written change.

    Wiki pages are written with an agent's own file tools, not by a verb here, so
    without this they would reach git only through sync's unattributed sweep. This is
    the swap for the log line an agent used to append by hand — same closed
    vocabulary, carried by the commit that actually made the change."""
    base = resolve_base(args)
    if args.verb not in AOS_VERBS:
        die(f"unknown aos-verb {args.verb!r} — one of "
            f"{', '.join(sorted(AOS_VERBS))}")
    missing = [p for p in args.path if not (base.root / p).exists()]
    if missing:
        die(f"no such path in the base: {', '.join(missing)}")
    agent, author, _ = acting(args, base)
    if not base.commit(args.verb, args.path, args.summary, agent, author):
        die("nothing to commit — those paths are unchanged", 1)
    print(f"committed: {args.verb} — {', '.join(args.path)}")


def cmd_history(args):
    """Recent activity — the orientation read log.md used to serve. Git already holds
    it; this only pins the format so it stays as parseable as the old grammar was."""
    base = resolve_base(args)
    if not is_repo(base.root):
        die("not a git repo — no history")
    fmt = ("%cI%x1f%an%x1f%cn%x1f%s%x1f"
           "%(trailers:key=aos-path,valueonly,separator=%x2C)")
    out = git(base.root, "log", f"-{args.limit}", f"--pretty={fmt}").stdout
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
