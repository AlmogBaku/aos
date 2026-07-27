"""Everything that reads or mutates a page once it is *in* the tree — not pending,
not raw. `search`/`links`/`index` read the page graph; `set`/`prune`/`archive`/
`verify` mutate it; `state` is per-principal wiki-adjacent bookkeeping, sharing the
query DSL with the read verbs.

`_collect_pages`/`_link_graph` are private helpers shared with `lint.py` (imported
from here rather than duplicated)."""

import re
import sqlite3
import datetime as _dt
from pathlib import Path

import yaml

from ..constants import WIKILINK_RE, UNIVERSAL_FIELDS, RAW_FIELDS, PENDING_FIELDS
from ..frontmatter import read_frontmatter, write_frontmatter
from ..query import query_of, match_query
from ..identity import die, today, git
from ..base import Base, resolve_base, acting


def _collect_pages(base: Base):
    pages = []
    for p in base.md_files(kinds=("wiki", "raw")):
        fm, body = read_frontmatter(p)
        fm = fm or {}
        pages.append({"rel": base.rel(p), "title": str(fm.get("title", p.stem)),
                      "aliases": [str(a) for a in (fm.get("aliases") or [])],
                      "description": str(fm.get("description", "")),
                      "body": body, "fm": fm})
    return pages


def cmd_search(args):
    base = resolve_base(args)
    where, without = query_of(args)
    # The filter narrows the candidate set, so it composes with the full-text ranking
    # rather than replacing it: `find` asks a metadata question, `search` a text one.
    pages = [pg for pg in _collect_pages(base)
             if match_query(pg["fm"], where, without)]
    q = args.query.strip()
    ql = q.lower()

    exact = [pg for pg in pages
             if ql == pg["title"].lower()
             or ql in [a.lower() for a in pg["aliases"]]]
    db = sqlite3.connect(":memory:")
    db.execute("CREATE VIRTUAL TABLE pages USING fts5(rel, title, description, body)")
    for pg in pages:
        db.execute("INSERT INTO pages VALUES (?,?,?,?)",
                   (pg["rel"], pg["title"], pg["description"], pg["body"]))
    fts_q = " OR ".join(f'"{t}"' for t in re.findall(r"\w+", q)) or f'"{q}"'
    try:
        rows = db.execute(
            "SELECT rel, title, snippet(pages, 3, '[', ']', '…', 12), bm25(pages) "
            "FROM pages WHERE pages MATCH ? ORDER BY bm25(pages) LIMIT ?",
            (fts_q, args.limit)).fetchall()
    except sqlite3.OperationalError:
        rows = []

    if exact:
        for pg in exact:
            print(f"EXISTS  {pg['rel']}  (exact title/alias match: {pg['title']})")
    seen = {pg["rel"] for pg in exact}
    for rel, title, snip, score in rows:
        if rel in seen:
            continue
        print(f"match   {rel}  [{title}]  {snip}")
    if not exact and not rows:
        print("no matches")
    print(f"-- create_safety: {'exists' if exact else ('probable' if rows else 'unknown')}")


def _link_graph(base: Base, where=None, without=None):
    """Return outlinks: rel -> set(rel). A query narrows which pages are *reported*,
    never which are resolvable — a link into a filtered-out page is still a link."""
    pages = list(base.md_files(kinds=("wiki", "raw")))
    stems = {}
    for p in pages:
        rel = base.rel(p)
        stems[rel[:-3]] = rel  # strip .md
    out = {}
    for p in pages:
        rel = base.rel(p)
        _, body = read_frontmatter(p)
        targets = set()
        for m in WIKILINK_RE.finditer(body):
            t = m.group(1).strip()
            if t.endswith(".md"):
                t = t[:-3]
            if t in stems:
                if stems[t] != rel:      # a self-link is not an inbound reference
                    targets.add(stems[t])
            else:
                # short-form: match by basename within the tree
                cands = [full for stem, full in stems.items()
                         if stem.split("/")[-1] == t]
                if len(cands) == 1:
                    targets.add(cands[0])
                else:
                    targets.add(f"!missing:{t}")
        out[rel] = targets
    return out


def cmd_links(args):
    base = resolve_base(args)
    where, without = query_of(args)
    graph = _link_graph(base)

    def selected(rel: str) -> bool:
        if not where and not without:
            return True
        fm, _ = read_frontmatter(base.root / rel)
        return bool(fm) and match_query(fm, where, without)

    if args.orphans:
        inbound = {t for targets in graph.values() for t in targets}
        for rel in sorted(graph):
            if rel not in inbound and not rel.startswith("_raw/") and selected(rel):
                print(f"orphan  {rel}")
        return
    page = args.page
    if page and not page.endswith(".md"):
        page += ".md"
    if page not in graph:
        die(f"unknown page {args.page!r}")
    print("outbound:")
    for t in sorted(graph[page]):
        print(f"  {t}")
    print("backlinks:")
    for rel, targets in sorted(graph.items()):
        if page in targets:
            print(f"  {rel}")


def cmd_index(args):
    base = resolve_base(args)
    name = base.cfg.get("name", base.root.name)
    lines = [f"# {name} — map of content", "",
             "> One line per page (from its `description:`); regenerated by "
             "`kb index rebuild`. An unlisted page is invisible.", ""]
    for zone in base.wiki_zones():
        zdir = base.root / zone
        lines.append(f"## {zone}")
        lines.append("")
        entries = []
        for p in sorted(zdir.rglob("*.md")):
            if "AGENTS" in p.name:
                continue
            fm, _ = read_frontmatter(p)
            fm = fm or {}
            stem = base.rel(p)[:-3]
            desc = fm.get("description") or fm.get("title") or p.stem
            entries.append(f"- [[{stem}]] — {desc}")
        lines += entries or ["*(empty)*"]
        lines.append("")
    (base.root / "index.md").write_text("\n".join(lines), encoding="utf-8")
    agent, author, _ = acting(args, base)
    base.commit("create", "index.md", "index rebuilt", agent, author)
    print(f"index.md rebuilt ({sum(1 for _ in base.md_files())} pages)")


def _in_base(base: Base, rel: str) -> Path:
    """Resolve a base-relative path, refusing anything that escapes the tree."""
    p = (base.root / rel).resolve()
    try:
        p.relative_to(base.root)
    except ValueError:
        die(f"{rel}: outside the base — refusing to write there", 13)
    return p


def cmd_set(args):
    """Generic frontmatter mutation, one attributed commit. Every key is validated
    against the base's schema, so `kb set` cannot quietly introduce a field lint will
    then flag as outside it."""
    base = resolve_base(args)
    agent, author, _ = acting(args, base)
    p = _in_base(base, args.path)
    if not p.exists():
        die(f"no such page: {args.path}")
    fm, body = read_frontmatter(p)
    if fm is None:
        die(f"{args.path}: no frontmatter to set (a page needs one first)")
    allowed = UNIVERSAL_FIELDS | RAW_FIELDS | PENDING_FIELDS | set(
        (base.cfg.get("frontmatter") or {}).get("extensions") or [])
    for pair in args.assignment:
        if "=" not in pair:
            die(f"{pair!r} doesn't parse as key=value")
        key, val = pair.split("=", 1)
        key, val = key.strip(), val.strip()
        root_key = key.split(".")[0]
        if root_key not in allowed:
            die(f"{root_key!r} is outside the base schema — add it to "
                f".kb/base.yml frontmatter.extensions first, or nest it under meta:",
                14)
        cur, parts = fm, key.split(".")
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
            if not isinstance(cur, dict):
                die(f"{key}: {part} is not a mapping")
        cur[parts[-1]] = yaml.safe_load(val)
    write_frontmatter(p, fm, body)
    base.commit("set", [base.rel(p)],
                f"{args.path}: {' '.join(args.assignment)[:80]}", agent, author)
    print(f"set: {base.rel(p)}  {' '.join(args.assignment)}")


def cmd_prune(args):
    """`expires:` is the ONLY thing kb knows about a page's lifetime. Passed means
    gone, and git is the undo. `due:` is a deadline (work-tracker's field, never
    interpreted here) and `review_by:` means "ask me again" — the opposite of expires.
    _raw/ never expires: source material is the trust chain."""
    base = resolve_base(args)
    agent, author, _ = acting(args, base)
    gone = []
    for p in base.md_files(kinds=("wiki",)):     # NOT raw
        fm, _ = read_frontmatter(p)
        exp = (fm or {}).get("expires")
        if not exp:
            continue
        try:
            if _dt.date.fromisoformat(str(exp)[:10]) > _dt.date.today():
                continue
        except ValueError:
            print(f"{base.rel(p)}: unparseable expires {exp!r} — left in place")
            continue
        gone.append(base.rel(p))
    if not gone:
        print("prune: nothing has expired.")
        return
    for rel in gone:
        print(f"pruned: {rel} (expired)")
    if args.dry_run:
        print(f"({len(gone)} would be pruned — dry run, nothing changed)")
        return
    for rel in gone:
        if git(base.root, "rm", "-q", "--", rel).returncode != 0:
            (base.root / rel).unlink()
    base.commit("prune", gone, f"{len(gone)} expired page(s)", agent, author)
    print(f"({len(gone)} pruned — git history is the undo)")


def cmd_archive(args):
    """A `git rm` plus an attributed commit carrying the reason. There is no _archive/
    directory: the history IS the archive, which is the whole argument for removing it.

    Note this is NOT `kb commit --verb archive` on a hand-move — that older form meant
    "I moved a file into _archive/", and the two mean opposite things now."""
    base = resolve_base(args)
    agent, author, _ = acting(args, base)
    rels = []
    for rel in args.path:
        p = _in_base(base, rel)
        if not p.exists():
            die(f"no such page: {rel}")
        rels.append(base.rel(p))
    for rel in rels:
        if git(base.root, "rm", "-q", "--", rel).returncode != 0:
            (base.root / rel).unlink()
    base.commit("archive", rels, f"{args.reason or 'archived'} ({len(rels)} page(s))",
                agent, author)
    for rel in rels:
        print(f"archived: {rel} — {args.reason or 'no reason given'}")
    print("(git history is the archive; nothing was copied anywhere)")


def cmd_verify(args):
    base = resolve_base(args)
    p = base.root / (args.page if args.page.endswith(".md") else args.page + ".md")
    fm, body = read_frontmatter(p)
    if fm is None:
        die(f"{args.page}: no frontmatter")
    fm["verified"] = True
    write_frontmatter(p, fm, body)
    agent, author, _ = acting(args, base)
    base.commit("verify", p, "user confirmed", agent, author)
    print(f"{base.rel(p)}: verified")


def cmd_state(args):
    base = resolve_base(args)
    agent, author, _ = acting(args, base)
    principal = author[1]           # the shard is one person's, not one grant row's
    st = base.load_state(principal)
    items = st["items"]
    sp = base.state_path(principal)

    def persist(summary: str):
        base.save_state(st, principal)
        base.commit("state", sp, summary, agent, author)

    if args.op == "show":
        # Here the query filters ITEMS, not files — an item is a dict, so match_query
        # works on it unchanged.
        where, without = query_of(args)

        def keep(data: dict) -> dict:
            if not where and not without:
                return data
            return {**data, "items": [it for it in (data.get("items") or [])
                                      if isinstance(it, dict)
                                      and match_query(it, where, without)]}

        if getattr(args, "all", False):
            # The union across shards is the team's current-truth view; each shard
            # still has exactly one writer, which is what keeps it mergeable.
            for p in base.state_paths():
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                print(f"# {base.rel(p)}")
                print(yaml.safe_dump(keep(data), sort_keys=False,
                                     allow_unicode=True).strip())
                print()
            return
        print(yaml.safe_dump(keep(st), sort_keys=False, allow_unicode=True).strip())
        return
    if args.op == "check":
        stale = []
        cutoff = _dt.date.today() - _dt.timedelta(days=args.stale_days)
        for it in items:
            since = str(it.get("since", ""))
            review = str(it.get("review_by", ""))
            reasons = []
            if since and since <= cutoff.isoformat():
                reasons.append(f"since {since} (> {args.stale_days}d)")
            if review and review <= today():
                reasons.append(f"review_by {review} passed")
            if reasons:
                stale.append((it, reasons))
        print(f"items: {len(items)}/{base.state_cap()}")
        for it, reasons in stale:
            print(f"stale: {it.get('note')!r} — {'; '.join(reasons)}")
        if not stale:
            print("no stale items")
        return
    if args.op == "add":
        if not args.note:
            die("state add needs --note")
        if len(items) >= base.state_cap():
            die(f"state is at its cap ({base.state_cap()}). Evict first "
                f"(`kb state drop`) — adding when full is an eviction decision.", 12)
        item = {"note": args.note}
        if args.ref:
            item["ref"] = args.ref
        item["since"] = today()
        if args.review_by:
            item["review_by"] = args.review_by
        items.append(item)
        persist(f"add: {args.note[:50]}")
        print(f"added ({len(items)}/{base.state_cap()})")
        return
    # bump / drop match by substring of note
    if not args.note:
        die(f"state {args.op} needs --note <substring>")
    exact = [i for i in items
             if str(i.get("note", "")).lower() == args.note.lower()]
    matches = exact or [i for i in items
                        if args.note.lower() in str(i.get("note", "")).lower()]
    if len(matches) != 1:
        die(f"--note must match exactly one item (matched {len(matches)})")
    it = matches[0]
    if args.op == "bump":
        it["since"] = today()
        persist(f"bump: {it['note'][:50]}")
        print("bumped")
    elif args.op == "drop":
        items.remove(it)
        persist(f"drop: {it['note'][:50]}")
        print(f"dropped ({len(items)}/{base.state_cap()})")
