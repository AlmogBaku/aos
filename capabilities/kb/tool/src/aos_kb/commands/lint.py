"""The deterministic check catalog. Report-only by default — the report is the
interface, and the exit code carries no verdict; `--ci` is the one exception.

Kept as its own module, ~340 lines, because it is the single largest verb in the
tool — importing `_link_graph` from `wiki.py` rather than duplicating it.

`_run_lint()` is a plain function taking explicit keyword arguments — not the typer
command itself — so `cmd_adopt` (in `lifecycle.py`) can call it directly with its own
defaults, rather than trying to invoke a wrapped typer `Command` object
programmatically. `cmd_lint` (the typer command) is a thin wrapper: resolve the base,
call `_run_lint`."""

import fnmatch
import re
import sys
import datetime as _dt
from typing import Annotated

import typer
import yaml

from ..constants import UNIVERSAL_FIELDS, RAW_FIELDS, PENDING_FIELDS, PENDING_KINDS, \
    WAITS_ON, WIKILINK_RE
from ..frontmatter import slugify, read_frontmatter
from ..identity import today, is_repo, git, sequencer_state, is_weak_principal, \
    principal_file, resolve_principal
from ..registry import load_registry
from ..base import Base, resolve_base
from .wiki import _link_graph

app = typer.Typer()


def _lint_pages(base: Base, critical: list, findings: list, info: list,
                types: set, extensions: set, graph: dict) -> list:
    """Per-page frontmatter/body checks + alias collisions + timeline shape. Returns
    the unverified-with-inbound-links list, reported later alongside `info` (its
    wording groups every such page into one line rather than one per page)."""
    titles_seen, alias_owner = {}, {}
    unverified_with_inbound = []
    inbound_count = {}
    for rel, targets in graph.items():
        for t in targets:
            inbound_count[t] = inbound_count.get(t, 0) + 1

    for p in base.md_files(kinds=("wiki",)):
        rel = base.rel(p)
        fm, body = read_frontmatter(p)
        if fm is None:
            critical.append(f"{rel}: frontmatter missing or unparseable")
            continue
        for req in ("title", "type", "created", "timestamp"):
            if req not in fm:
                findings.append(f"{rel}: missing required field {req!r}")
        if "description" not in fm:
            info.append(f"{rel}: no description (index entries come from it)")
        if types and fm.get("type") not in types:
            findings.append(f"{rel}: type {fm.get('type')!r} not in base.yml types")
        unknown = set(fm) - UNIVERSAL_FIELDS - extensions - RAW_FIELDS \
            - PENDING_FIELDS
        if unknown:
            findings.append(f"{rel}: fields outside schema (move under meta:): "
                            f"{sorted(unknown)}")
        if not body.strip():
            findings.append(f"{rel}: empty page")
        # alias collisions
        t = str(fm.get("title", "")).lower()
        if t:
            titles_seen.setdefault(t, []).append(rel)
        for a in (fm.get("aliases") or []):
            a = str(a).lower()
            if a in alias_owner and alias_owner[a] != rel:
                critical.append(f"alias collision: {a!r} claimed by {alias_owner[a]} "
                                f"and {rel}")
            alias_owner[a] = rel
        if fm.get("verified") is False and inbound_count.get(rel):
            unverified_with_inbound.append(f"{rel} ({inbound_count[rel]} inbound)")
        # timeline shape (fenced code blocks don't count)
        unfenced = re.sub(r"```.*?```", "", body, flags=re.S)
        if "## Timeline" in unfenced:
            tail = unfenced.split("## Timeline", 1)[1]
            for line in [l for l in tail.splitlines() if l.strip()][:20]:
                if line.startswith("#"):
                    findings.append(f"{rel}: '## Timeline' is not the last section")
                    break
                if line.strip().startswith("-") and not re.match(
                        r"-\s*\d{4}-\d{2}-\d{2}", line.strip()):
                    findings.append(f"{rel}: timeline entry not dated: {line.strip()[:40]!r}")
                    break
        if "Contested" in body:
            info.append(f"{rel}: carries a Contested marker (unresolved by design)")
        # The stale-seedling rule is gone with growth_stage, its only reader. `expires:`
        # is the whole of what kb knows about a page's lifetime, and nothing else keys
        # on age.

    for title, rels in titles_seen.items():
        if len(rels) > 1:
            critical.append(f"duplicate title {title!r}: {rels}")
    return unverified_with_inbound


def _lint_links_and_index(base: Base, findings: list, graph: dict) -> None:
    """Broken wikilinks + index.md drift in both directions."""
    for rel, targets in graph.items():
        for t in targets:
            if t.startswith("!missing:"):
                findings.append(f"{rel}: broken wikilink [[{t[9:]}]]")
    index_text = (base.root / "index.md").read_text(encoding="utf-8") \
        if (base.root / "index.md").exists() else ""
    index_links = {t[:-3] if t.endswith(".md") else t
                   for t in (m.group(1).strip()
                             for m in WIKILINK_RE.finditer(index_text))}
    for p in base.md_files(kinds=("wiki",)):
        rel = base.rel(p)
        stem = rel[:-3]
        if stem not in index_links:
            findings.append(f"index drift: {rel} not listed in index.md (invisible)")
    for m in WIKILINK_RE.finditer(index_text):
        t = m.group(1).strip()
        if not (base.root / f"{t}.md").exists() and not (base.root / t).exists():
            findings.append(f"index drift: dead index entry [[{t}]]")


def _lint_raw(base: Base, findings: list) -> None:
    """_raw/ is flat and immutable; there is no triage: to validate, because being
    here IS "ingested"."""
    for p in base.raw_dir.rglob("*.md") if base.raw_dir.is_dir() else []:
        if "AGENTS" in p.name:
            continue
        rel = base.rel(p)
        fm, _ = read_frontmatter(p)
        if fm is None:
            findings.append(f"{rel}: raw file without frontmatter")
            continue
        if p.parent != base.raw_dir:
            findings.append(f"{rel}: _raw/ is flat — type: and source: already carry "
                            f"what a subdirectory would say")
        if "source_sha256" not in fm:
            findings.append(f"{rel}: missing source_sha256 (dedup key)")
        for gone in ("kind", "waits_on"):
            if gone in fm:
                findings.append(f"{rel}: ingested files carry no {gone}: — that field "
                                f"belongs to the queue the item has left")


def _lint_pending(base: Base, critical: list, findings: list,
                  stale_pending_days: int) -> None:
    for p in sorted(base.pending_dir.glob("*.md")) if base.pending_dir.is_dir() else []:
        rel = base.rel(p)
        fm, _ = read_frontmatter(p)
        if fm is None:
            findings.append(f"{rel}: pending entry without frontmatter")
            continue
        if fm.get("kind") not in PENDING_KINDS:
            findings.append(f"{rel}: kind {fm.get('kind')!r} not in "
                            f"{sorted(PENDING_KINDS)}")
        if fm.get("waits_on") not in WAITS_ON:
            findings.append(f"{rel}: waits_on {fm.get('waits_on')!r} not in "
                            f"{sorted(WAITS_ON)}")
        if fm.get("failed"):
            critical.append(f"{rel}: capture failed ({fm['failed']}) — it stays in the "
                            f"queue until a human or a retry clears it")
        created = str(fm.get("created", ""))
        if fm.get("waits_on") == "human" and created:
            try:
                age = (_dt.date.today() - _dt.date.fromisoformat(created[:10])).days
                if age > stale_pending_days:
                    findings.append(f"{rel}: waiting on a human for {age}d — nothing "
                                    f"will move it but a person")
            except ValueError:
                findings.append(f"{rel}: unparseable created {created!r}")


def _lint_backups_and_lfs(base: Base, critical: list, findings: list) -> None:
    lfs_patterns = []
    ga = base.root / ".gitattributes"
    if ga.exists():
        for line in ga.read_text(encoding="utf-8").splitlines():
            if "filter=lfs" in line and not line.strip().startswith("#"):
                lfs_patterns.append(line.split()[0])
    for p in base.root.rglob("*"):
        if ".git" in p.parts or ".base" in p.parts or not p.is_file():
            continue
        if p.name.endswith(".bak") or ".backup." in p.name:
            critical.append(f"{base.rel(p)}: backup file — git history is the archive")
        if p.suffix not in (".md", ".yaml", ".yml", ".txt", ".json", "") \
                and p.stat().st_size > 1024 * 1024:
            if not any(fnmatch.fnmatch(p.name, pat) for pat in lfs_patterns):
                findings.append(f"{base.rel(p)}: large non-text file "
                                f"({p.stat().st_size // 1024}KB) not matching any "
                                f"LFS pattern in .gitattributes")


def _lint_state(base: Base, critical: list, findings: list) -> None:
    """One file per principal on a shared base, so each is checked separately and
    each genuinely has one writer."""
    state_files = base.state_paths()
    if state_files:
        newest = max((p.stat().st_mtime for p in base.md_files(kinds=("wiki",))),
                     default=0)
        for sp in state_files:
            rel = base.rel(sp)
            data = yaml.safe_load(sp.read_text(encoding="utf-8")) or {}
            its = data.get("items") or []
            if len(its) > base.state_cap():
                critical.append(f"{rel} over cap: {len(its)}/{base.state_cap()}")
            for it in its:
                if not isinstance(it, dict) or "note" not in it or "since" not in it:
                    findings.append(f"{rel}: malformed item {it!r}")
            if newest and newest > sp.stat().st_mtime + 60:
                findings.append(f"state_stale: wiki pages changed after {rel} — "
                                f"refresh the attention window")
    else:
        findings.append("no state file (.kb/state/<principal>.yml)")


def _lint_git_health(base: Base, critical: list, findings: list) -> None:
    """git is the audit substrate, so its condition is a lint subject."""
    if is_repo(base.root):
        seq = sequencer_state(base.root)
        if seq:
            critical.append(f"git is mid-{seq}: finish or abort it. Nothing can sync "
                            f"while that state directory is there, and staging the "
                            f"worktree now would commit conflict markers")
        dirty = git(base.root, "status", "--porcelain").stdout.strip()
        if dirty:
            findings.append(f"uncommitted changes ({len(dirty.splitlines())} paths) — "
                            f"every write is meant to be its own attributed commit "
                            f"(`kb commit`)")


def _lint_grants_via_grammar(base: Base, findings: list) -> None:
    """Grants hygiene: `via` grammar, since revocation depends on it."""
    agents_md = base.root / "AGENTS.md"
    if agents_md.exists():
        in_grants = in_table = False
        for i, line in enumerate(agents_md.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("## "):
                in_grants = line.strip().lower() == "## grants"
                continue
            if not in_grants or not line.strip().startswith("|"):
                in_table = in_table and not line.strip() == ""
                continue
            cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            if cells and (cells[0] == "subject" or set("".join(cells)) <= set("-: ")):
                in_table = True
                continue
            if in_table and len(cells) >= 6:
                via = cells[5]
                if via not in ("—", "-", "") and not re.match(
                        r"^[a-z0-9-]+@\d+\.\d+\.\d+$", via):
                    findings.append(f"AGENTS.md:{i}: grant via {via!r} doesn't parse "
                                    f"as <capability>@<x.y.z> or — (revocation "
                                    f"deletes rows by via match)")


def _lint_grants_audit(base: Base, global_opts, critical: list, findings: list,
                       info: list, audit_days: int) -> str:
    """Authorship x grants over recent commits.

    This is a real check now rather than one deferred to a cross-check that was
    never built. Every write is its own commit, so nothing is batched under one
    identity and there is no exemption to make: the *committer* is the acting agent
    (the subject a grant names) and the *author* is the principal whose knowledge it
    is. A commit with neither is the finding. Returns the resolved principal id, so
    the caller's principal-drift check reuses it rather than resolving twice."""
    grants = base.grants()
    # The reporting half of "the principal never blocks": a synthesized or placeholder
    # identity authors every write, and the write proceeds — this is where it surfaces.
    pid = resolve_principal(global_opts, base.cfg.get("name", base.root.name),
                            base.root, persist=False)
    if is_weak_principal(pid):
        findings.append(f"weak principal {pid!r} — a synthesized or placeholder "
                        f"identity authors every write. Fix it in "
                        f"{principal_file()} or run kb's onboarding interview")

    # Principal drift: a shard whose owner is neither the current principal nor named
    # in any grant row is somebody who left, or a typo that silently made a new person.
    # Only sharded state has an owner in its filename; the flat file belongs to
    # whoever holds the base, so its name says nothing about drift.
    known = {r.subject.strip().lower() for r in grants} | {pid.lower(), "user"}
    known_slugs = {slugify(k) for k in known}
    for sp in (base.state_paths() if base.audience() == "shared" else []):
        who = sp.stem
        if who.lower() not in known_slugs:
            findings.append(f"{base.rel(sp)}: orphaned state shard — {who!r} is "
                            f"neither the current principal nor named in any grant row")

    if is_repo(base.root):
        try:
            out = git(base.root, "log", f"--since={audit_days} days ago",
                      "--pretty=%H%x1f%an%x1f%ae%x1f%cn%x1f%s", "--name-only").stdout
            sha = committer = None
            skip_commit = False
            for line in out.splitlines():
                if "\x1f" in line:
                    sha, _an, ae, committer, subject = line.split("\x1f", 4)
                    # `bootstrap` scaffolds the tree before any grant row exists;
                    # `migrate` carries a layout 1 tree whose rows named layout 1
                    # paths — the same "before this table meant anything" exemption.
                    skip_commit = subject.startswith(("bootstrap", "migrate:"))
                    if subject.startswith("sweep:"):
                        findings.append(
                            f"commit {sha[:8]}: {subject} — swept by sync rather than "
                            f"written through a verb, so no acting subject was "
                            f"recorded. Use `kb commit` after a hand-write")
                    continue
                if not line.strip() or skip_commit or not grants:
                    continue
                path = line.strip()
                if path.startswith(".kb/cache/"):
                    continue
                subj = committer if committer.startswith(
                    ("agent:", "capability:", "user")) else f"agent:{committer}"
                if subj == "user" or base.grant_check(subj, "write", path) \
                        or base.grant_check(subj, "route-into", path):
                    continue
                critical.append(f"grants audit: {subj} wrote {path} with no matching "
                                f"grant (commit {sha[:8]})")
        except Exception as e:  # noqa: BLE001 — audit must not crash the lint
            info.append(f"grants audit not checkable: {e}")
    return pid


def _lint_routing(base: Base, global_opts, critical: list, findings: list) -> None:
    """§4.5 layer 2: no LLM-routed write may ever reach a shared base. The exclusion
    is a list filter, not a threshold, so the check is an existence test — and it is
    the falsifiable half of the rule the route skill states in prose."""
    bar = float((load_registry(global_opts) or {}).get("confidence_bar", 0.7) or 0.7)
    # Both halves of the capture path: an LLM-routed capture is a violation the moment
    # it is written, not only once it is ingested — checking _raw/ alone would let one
    # sit in the queue unreported.
    routable = (list(base.raw_dir.rglob("*.md")) if base.raw_dir.is_dir() else []) \
        + (sorted(base.pending_dir.glob("*.md")) if base.pending_dir.is_dir() else [])
    for p in routable:
        if "AGENTS" in p.name:
            continue
        fm, _ = read_frontmatter(p)
        kr = (fm or {}).get("kb_routing")
        if not isinstance(kr, dict):
            continue
        rel = base.rel(p)
        method = kr.get("method")
        if method == "llm" and base.audience() == "shared":
            critical.append(f"{rel}: kb_routing.method: llm in an audience: shared "
                            f"base — no LLM-routed write may ever land here")
        if method not in (None, "explicit", "rule", "llm", "default"):
            findings.append(f"{rel}: kb_routing.method {method!r} is not one of "
                            f"explicit|rule|llm|default")
        if method == "llm":
            conf = kr.get("confidence")
            if not isinstance(conf, (int, float)):
                findings.append(f"{rel}: kb_routing.method: llm without a confidence")
            elif conf < bar and kr.get("status") == "routed":
                findings.append(f"{rel}: kb_routing confidence {conf} below the bar "
                                f"({bar}) but status: routed")


def _run_lint(base: Base, global_opts, *, audit_days: int = 8,
             stale_pending_days: int = 14, ci: bool = False) -> None:
    critical, findings, info = [], [], []
    types = set(base.cfg.get("types") or [])
    extensions = set((base.cfg.get("frontmatter") or {}).get("extensions") or [])
    graph = _link_graph(base)

    unverified_with_inbound = _lint_pages(base, critical, findings, info,
                                          types, extensions, graph)
    _lint_links_and_index(base, findings, graph)
    _lint_raw(base, findings)
    _lint_pending(base, critical, findings, stale_pending_days)
    _lint_backups_and_lfs(base, critical, findings)
    _lint_state(base, critical, findings)
    _lint_git_health(base, critical, findings)
    _lint_grants_via_grammar(base, findings)
    _lint_grants_audit(base, global_opts, critical, findings, info, audit_days)
    _lint_routing(base, global_opts, critical, findings)

    if unverified_with_inbound:
        info.append("unverified pages with inbound links (don't build on them alone): "
                    + ", ".join(unverified_with_inbound))

    # report
    lines = [f"# lint — {base.cfg.get('name', base.root.name)} — {today()}", ""]
    lines.append(f"## Critical ({len(critical)})")
    lines += [f"- {c}" for c in critical] or ["- none"]
    lines.append(f"\n## Findings ({len(findings)})")
    lines += [f"- {f}" for f in findings] or ["- none"]
    lines.append(f"\n## Info ({len(info)})")
    lines += [f"- {i}" for i in info] or ["- none"]
    report = "\n".join(lines) + "\n"
    print(report, end="")

    # The report IS the interface. There used to be a --write-report flag that committed
    # this same text into the base as a dated file; nothing ever read it, and the weekly
    # job's real need was never a file but for criticals to become work someone sees —
    # which is what `kb pending add --kind finding` does.
    # Report-only by default: the report is the interface, and the exit code carries no
    # verdict. `--ci` is the one exception, and it outlived the CI janitor it was built
    # for: a user wiring lint into their own hook or Action needs an exit code, and the
    # alternative is parsing the report text. The default staying report-only is the
    # contract; --ci is what makes that contract falsifiable rather than a preference.
    if ci and critical:
        sys.exit(1)


@app.command("lint", help="the deterministic check catalog (report-only; the "
                         "report is the interface)")
def cmd_lint(
    ctx: typer.Context,
    audit_days: int = 8,
    stale_pending_days: Annotated[int, typer.Option(
        help="an entry waiting on a human longer than this is a finding")] = 14,
    ci: Annotated[bool, typer.Option(
        help="exit 1 on any critical — for a hook or an unattended runner that "
             "needs a verdict rather than a report")] = False,
):
    base = resolve_base(ctx.obj)
    _run_lint(base, ctx.obj, audit_days=audit_days,
             stale_pending_days=stale_pending_days, ci=ci)
