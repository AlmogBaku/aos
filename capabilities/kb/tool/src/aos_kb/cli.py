"""kb — the kb capability's deterministic executor.

Deterministic operations ONLY: this tool never calls an LLM and never invokes an
agent. Skills call it; it answers in exit codes, stdout, and files — files are the
async message bus (a sync conflict becomes a _ops/needs-review/ entry, not a
callback). Every write verb makes its own commit: author = the human principal whose
knowledge it is, committer = the acting agent, with aos-verb/aos-path trailers. Git is
the single audit substrate — there is no log.md.

Every shared record is one file per record (captures, review-queue entries, per-
principal state). That is what keeps a base conflict-free when several machines — or
several people — sync it; nothing here relies on a merge driver.

Reports (lint, adopt) are report-only and written for an LLM to judge: the report is
the interface. Search/links exit codes carry no information beyond "ran".

Layout guard: every base-scoped verb validates BASE.yaml `layout` and fails loudly
on mismatch — never path-guesses across format generations.

Spec: design/kb-methodology.md (spec branch). Contract = verb set + boundary; the
implementation language is a build choice.
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import random
import re
import sqlite3
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import yaml

VERSION = "0.7.0"
LAYOUT = 1
# The closed `aos-verb` trailer vocabulary — the same words the five-field log.md
# grammar used, now carried by the commit that made the change.
AOS_VERBS = {
    "create", "promote", "merge", "archive", "flag", "resolve", "sync-conflict",
    "lint", "route", "refuse", "capture", "state", "verify", "bootstrap",
}
UNIVERSAL_FIELDS = {"title", "description", "type", "created", "timestamp", "tags",
                    "aliases", "verified", "origin", "growth_stage", "meta"}
RAW_FIELDS = {"source", "source_sha256", "captured_at", "triage", "kb_routing",
              "captured_by", "source_origin"}
TRIAGE_STATES = {"pending", "done", "failed"}
WIKILINK_RE = re.compile(r"\[\[([^\]|#\n]+?)(?:[|#][^\]]*)?\]\]")
# Dedup is scoped to the acting principal: same principal, same sha256, no new file —
# import/capture idempotency depends on it, and the flaky-client double-send is the
# common case. It is NOT global: on a base several people share, a global scan drops a
# second person's identical capture and discloses the first person's path.


# ---------------------------------------------------------------- helpers

def now_ts() -> str:
    return _dt.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M%z")[:-2] + ":" + \
        _dt.datetime.now().astimezone().strftime("%z")[-2:]


def today() -> str:
    return _dt.date.today().isoformat()


def die(msg: str, code: int = 1):
    print(f"base: error: {msg}", file=sys.stderr)
    sys.exit(code)


def slugify(text: str, max_len: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].strip("-") or "item"


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.S)


def read_frontmatter(path: Path):
    """Return (frontmatter dict or None, body str). Tolerant: bad YAML -> None.
    One parser for both halves: the same regex bounds the fm block and the body."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None, ""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, text
    if not isinstance(fm, dict):
        return None, text
    return fm, text[m.end():]


def write_frontmatter(path: Path, fm: dict, body: str):
    front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{front}\n---\n{body}", encoding="utf-8")


def glob_to_re(pattern: str) -> re.Pattern:
    """git-style glob: ** crosses /, * does not."""
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if pattern[i:i + 2] == "**":
                i += 2
                if i < len(pattern) and pattern[i] == "/":
                    i += 1
                    out.append("(?:.*/)?")   # any depth, but never a name suffix
                else:
                    out.append(".*")
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def find_household() -> Path | None:
    """The household root: <home>/{upstream,personal,.aos}. `.aos/` is the marker —
    checked before any capabilities/ heuristic, so a render inside personal/ (which
    also carries capabilities/) is never mistaken for the household or for upstream."""
    env = os.environ.get("AOS_HOME")
    if env:
        return Path(env).expanduser()
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / ".aos").is_dir():
            return p
    return None


def find_upstream_root() -> Path:
    home = find_household()
    if home:
        return home / "upstream"
    # not inside a household: a bare kit checkout is its own upstream root
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "capabilities" / "kb" / "CAPABILITY.md").is_file():
            return p
    return Path.home() / "aos" / "upstream"


def find_personal_root() -> Path:
    home = find_household()
    if home:
        return home / "personal"
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "kb-registry.yaml").exists():
            return p
    return Path.home() / "aos" / "personal"


def registry_path(args) -> Path:
    if getattr(args, "registry", None):
        return Path(args.registry).expanduser()
    env = os.environ.get("AOS_REGISTRY")
    if env:
        return Path(env).expanduser()
    return find_personal_root() / "kb-registry.yaml"


def load_registry(args) -> dict:
    p = registry_path(args)
    if not p.exists():
        return {"default": None, "kbs": []}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    data.setdefault("kbs", [])
    return data


def save_registry(args, data: dict):
    p = registry_path(args)
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                 encoding="utf-8")


def agent_subject(args) -> str:
    return getattr(args, "agent", None) or os.environ.get("AOS_AGENT", "agent:main")


def agent_email(subject: str) -> str:
    """A syntactically valid address for an agent subject. The subject itself is the
    committer *name*, so `git log %cn` reads back as the subject with no parsing."""
    local = re.sub(r"[^a-zA-Z0-9._-]+", "-", subject).strip("-").lower() or "agent"
    return f"{local}@agents.local"


def git(root: Path, *argv) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], cwd=root, capture_output=True,
                          text=True, check=False)


def is_repo(root: Path) -> bool:
    return (root / ".git").exists()


def author_identity(args, root: Path) -> tuple[str, str]:
    """git's `author` — the human whose knowledge this is. We read the identity they
    already have rather than inventing one; the env overrides exist for service
    accounts and tests. Empty means "no identity configured", which the caller turns
    into an unattributed commit that lint reports."""
    name = getattr(args, "author_name", None) or os.environ.get("AOS_PRINCIPAL_NAME")
    email = getattr(args, "author_email", None) or os.environ.get("AOS_PRINCIPAL_EMAIL")
    if not name:
        name = git(root, "config", "user.name").stdout.strip()
    if not email:
        email = git(root, "config", "user.email").stdout.strip()
    return name, email


SEQUENCER_STATES = ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD",
                    "REVERT_HEAD")


def sequencer_state(root: Path) -> str | None:
    """Any operation left mid-flight. `git status --porcelain=v2` does NOT report
    these — its documented headers are branch.* only — so the state paths are the
    reliable test, which is what git's own git-prompt.sh uses. Staging a worktree in
    this condition commits conflict markers, and git then refuses to start another
    rebase over the old one ("I am stopping in case you still have something
    valuable there"), so the next tick fails forever."""
    for s in SEQUENCER_STATES:
        p = git(root, "rev-parse", "--git-path", s).stdout.strip()
        if p and (root / p).exists():
            return s
    return None


class Base:
    """One base on disk, layout-checked."""

    def __init__(self, root: Path, check_layout: bool = True):
        self.root = root.resolve()
        cfg_path = self.root / "BASE.yaml"
        if not cfg_path.exists():
            die(f"{self.root} has no BASE.yaml — not a base (adopt it first?)", 10)
        self.cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        if check_layout:
            layout = self.cfg.get("layout")
            if layout != LAYOUT:
                die(f"{self.root}: BASE.yaml layout={layout!r}, this tool speaks "
                    f"layout={LAYOUT}. Refusing to guess — run a migration.", 11)

    # -- structure ---------------------------------------------------------
    def zones(self) -> dict:
        return self.cfg.get("zones", {}) or {}

    def wiki_zones(self):
        return [z for z, d in self.zones().items()
                if isinstance(d, dict) and d.get("kind") == "wiki"]

    def md_files(self, kinds=("wiki",)):
        for zone, d in self.zones().items():
            if not isinstance(d, dict) or d.get("kind") not in kinds:
                continue
            zdir = self.root / zone
            if zdir.is_dir():
                for p in sorted(zdir.rglob("*.md")):
                    if "AGENTS" in p.name:
                        continue
                    yield p

    def rel(self, p: Path) -> str:
        return str(p.relative_to(self.root))

    # -- identity ----------------------------------------------------------
    def audience(self) -> str:
        return self.cfg.get("audience", "private")

    def principals(self) -> dict:
        """email -> grants subject. Base-side truth that travels with the repo, like
        `audience` — so every member pulling the base sees the same roster. Absent is
        the single-human case: everyone maps to the existing `user` subject, so a
        private base needs no roster and nothing changes for it."""
        p = self.cfg.get("principals")
        if not isinstance(p, dict):
            return {}
        return {str(k).strip().lower(): str(v).strip() for k, v in p.items()}

    def principal_subject(self, email: str) -> str:
        return self.principals().get((email or "").strip().lower(), "user")

    # -- commits -----------------------------------------------------------
    def commit(self, verb: str, paths, summary: str, agent: str,
               author: tuple[str, str] | None = None) -> bool:
        """One write, one commit — git is the audit substrate, so there is nothing to
        cross-check it against and nothing to conflict on.

        Author = the human whose knowledge it is; committer = the acting agent. That
        is git's own two-identity model ("who wrote it" vs "who applied it"), it
        survives rebase (which preserves the author and rewrites the committer), and
        forges show the author in the byline and in blame. Structured detail rides
        trailers because they survive rebase and cherry-pick; `git notes` would not —
        notes are not even pushed or fetched by default.
        """
        assert verb in AOS_VERBS, f"illegal aos-verb {verb}"
        if not is_repo(self.root):
            return False
        items = [paths] if isinstance(paths, (str, Path)) else list(paths)
        rels = [p if isinstance(p, str) else self.rel(p) for p in items]
        if not rels:
            return False
        trailers = "\n".join(f"aos-path: {r}" for r in rels)
        msg = f"{verb}: {summary}\n\naos-verb: {verb}\n{trailers}\n"

        env = dict(os.environ)
        env["GIT_COMMITTER_NAME"] = agent
        env["GIT_COMMITTER_EMAIL"] = agent_email(agent)
        argv = ["git", "add", "--"] + rels
        subprocess.run(argv, cwd=self.root, capture_output=True, check=False)
        commit_argv = ["git", "commit", "-q", "-m", msg]
        name, email = author or (None, None)
        if name and email:
            commit_argv += [f"--author={name} <{email}>"]
        else:
            # No identity configured: the commit still lands (data safety first) with
            # the agent as author, and lint reports it as unattributed.
            env["GIT_AUTHOR_NAME"] = agent
            env["GIT_AUTHOR_EMAIL"] = agent_email(agent)
        commit_argv += ["--"] + rels
        r = subprocess.run(commit_argv, cwd=self.root, capture_output=True,
                           text=True, check=False, env=env)
        return r.returncode == 0

    def review(self, title: str, body: str, agent: str = "") -> Path:
        """One file per review-queue entry. A single appended queue file is written by
        every agent on every machine, which is precisely the shape that conflicts on
        every sync; distinct filenames never do. The queue is a view over the
        directory, exactly like the inbox is a view over raw/captures/."""
        d = self.root / "_ops" / "needs-review"
        d.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
        slug = slugify(title)
        dst = d / f"{stamp}-{slug}.md"
        n = 2
        while dst.exists():
            dst = d / f"{stamp}-{slug}-{n}.md"
            n += 1
        fm = {"title": title, "created": today(), "raised_by": agent or "unknown",
              "status": "open"}
        write_frontmatter(dst, fm, body if body.endswith("\n") else body + "\n")
        return dst

    # -- state -------------------------------------------------------------
    def state_path(self, principal: str | None = None) -> Path:
        """A shared base shards state per principal. The rolling attention window is
        one person's by nature, and a single file rewritten in place by everyone is
        the one shape git cannot merge. Sharding makes methodology §7's single writer
        literally true, while "the team's current-truth" survives as the union of the
        shards. A private base keeps the flat file — nothing changes for it."""
        if self.audience() != "shared":
            return self.root / "state.yaml"
        return self.root / "state" / f"{slugify(principal or 'user')}.yaml"

    def state_paths(self) -> list[Path]:
        """Every state file in the base — the union view."""
        if self.audience() != "shared":
            p = self.root / "state.yaml"
            return [p] if p.exists() else []
        d = self.root / "state"
        return sorted(d.glob("*.yaml")) if d.is_dir() else []

    def load_state(self, principal: str | None = None) -> dict:
        p = self.state_path(principal)
        if not p.exists():
            return {"items": []}
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        data.setdefault("items", [])
        return data

    def save_state(self, data: dict, principal: str | None = None):
        header = ("# state — rolling attention window. One-line items pointing "
                  "into the wiki pages.\n# Managed via `kb state ...`; capped by "
                  "BASE.yaml state.max_items; git history is the archive.\n")
        p = self.state_path(principal)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(header + yaml.safe_dump(data, sort_keys=False,
                                             allow_unicode=True), encoding="utf-8")

    def state_cap(self) -> int:
        return int((self.cfg.get("state") or {}).get("max_items", 20))

    # -- grants ------------------------------------------------------------
    def grants(self):
        """Parse the first markdown table under '## Grants' in AGENTS.md."""
        agents_md = self.root / "AGENTS.md"
        if not agents_md.exists():
            return []
        rows, in_section, in_table = [], False, False
        for line in agents_md.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                in_section = line.strip().lower() == "## grants"
                continue
            if not in_section:
                continue
            if line.strip().startswith("|"):
                cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
                if set("".join(cells)) <= set("-: ") or cells[0] == "subject":
                    in_table = True
                    continue
                if in_table and len(cells) >= 3:
                    rows.append({"subject": cells[0], "object": cells[1],
                                 "verbs": cells[2].split()})
            elif in_table and line.strip():
                break
        return rows

    def grant_check(self, subject: str, verb: str, path: str) -> bool:
        for row in self.grants():
            subj_ok = row["subject"] == subject or (
                row["subject"] == "*" and subject != "(unregistered)")
            if not subj_ok or verb not in row["verbs"]:
                continue
            for pat in row["object"].split():
                if glob_to_re(pat).match(path):
                    return True
        return False


def resolve_base(args) -> Base:
    if getattr(args, "base", None):
        name_or_path = args.base
        p = Path(name_or_path).expanduser()
        if p.is_dir():
            return Base(p)
        reg = load_registry(args)
        for kb in reg["kbs"]:
            if kb.get("name") == name_or_path:
                return Base(Path(kb["path"]).expanduser())
        die(f"unknown base {name_or_path!r} (not a path, not in the registry)")
    # cwd inside a base?
    cur = Path.cwd()
    for p in [cur, *cur.parents]:
        if (p / "BASE.yaml").exists():
            return Base(p)
    reg = load_registry(args)
    default = reg.get("default")
    for kb in reg["kbs"]:
        if kb.get("name") == default:
            return Base(Path(kb["path"]).expanduser())
    die("no base: pass --base <name|path>, cd into one, or set a registry default")


def acting(args, base: Base) -> tuple[str, tuple[str, str], str]:
    """(agent subject, git author identity, principal subject) for this invocation.

    The agent is the committer, the author identity is the human's own, and the
    principal subject is what the grants table names. On a base with no roster —
    every private base — the principal is `user`, so nothing changes."""
    agent = agent_subject(args)
    author = author_identity(args, base.root)
    return agent, author, base.principal_subject(author[1])


# ---------------------------------------------------------------- verbs

def cmd_init(args):
    root = Path(args.path).expanduser().resolve()
    if (root / "BASE.yaml").exists():
        die(f"{root} already has a BASE.yaml")
    tpl = Path(args.templates).expanduser() if args.templates else \
        find_upstream_root() / "capabilities" / "kb" / "skills" / "init" / "templates"
    if not (tpl / "BASE.yaml").exists():
        die(f"templates not found at {tpl} (pass --templates)")
    root.mkdir(parents=True, exist_ok=True)

    subs = {"{{name}}": args.name, "{{today}}": today(),
            "{{version}}": args.kb_version, "{{audience}}": args.audience,
            "{{purpose}}": (args.purpose or "").strip(),
            "{{sync_mode}}": args.sync}

    def render(src: Path, dst: Path):
        text = src.read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(k, v)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")

    for name in ["BASE.yaml", "AGENTS.md", "index.md"]:
        render(tpl / name, root / name)

    base = Base(root)
    # A shared base shards state per principal; a private one keeps the flat file.
    render(tpl / "state.yaml", base.state_path())

    for zone, d in base.zones().items():
        (root / zone).mkdir(exist_ok=True)
        zone_tpl = tpl / "zones" / f"{zone}.AGENTS.md"
        if zone_tpl.exists():
            render(zone_tpl, root / zone / "AGENTS.md")
        for sub in (d or {}).get("subdirs", []) if isinstance(d, dict) else []:
            (root / zone / sub).mkdir(exist_ok=True)
    (root / "raw" / "captures").mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text(".base/\n", encoding="utf-8")
    if (tpl / "gitattributes").exists():
        render(tpl / "gitattributes", root / ".gitattributes")

    subprocess.run(["git", "init", "-q"], cwd=root, check=False)
    lfs = subprocess.run(["git", "lfs", "version"], capture_output=True, check=False)
    if lfs.returncode == 0:
        subprocess.run(["git", "lfs", "install", "--local"], cwd=root,
                       capture_output=True, check=False)
    else:
        print("note: git-lfs not installed — large non-text files won't be "
              "LFS-tracked until it is (`git lfs install --local` later).")
    # The user's own git identity authors every write from here on. We deliberately do
    # NOT overwrite it with a per-base agent identity: that erased the one attribution
    # git gives for free, and on a base two people share it made both of them the same
    # author. The acting agent is recorded as the committer instead.
    who = author_identity(args, root)
    if not all(who):
        print("note: no git identity configured — writes will be attributed to the "
              "acting agent and reported as unattributed by `kb lint`. Set "
              "`git config --global user.name` and `user.email`.")
    if args.remote:
        subprocess.run(["git", "remote", "add", "origin", args.remote],
                       cwd=root, check=False)

    reg = load_registry(args)
    existing = next((k for k in reg["kbs"] if k.get("name") == args.name), None)
    if existing:
        # A pre-seeded registry entry (interview ran first) is fine iff it points at
        # this path and the tree doesn't exist yet — init fills it in. Anything else
        # is a genuine duplicate.
        if Path(existing.get("path", "")).expanduser().resolve() != root:
            die(f"base {args.name!r} already registered at a different path")
        existing.setdefault("tag", args.tag or args.name)
        if (args.purpose or "").strip():
            existing["purpose"] = args.purpose.strip()
    else:
        entry = {"name": args.name, "tag": args.tag or args.name,
                 "path": str(root), "remote": args.remote,
                 "sync": args.sync, "audience": args.audience,
                 "methodology": "karpathy-llm-wiki",
                 "purpose": (args.purpose or "").strip(),
                 "routing": {"channels": [], "keywords": []}}
        reg["kbs"].append(entry)
    if args.default or not reg.get("default"):
        reg["default"] = args.name
    reg.setdefault("confidence_bar", 0.7)
    save_registry(args, reg)

    base.commit("bootstrap", ".", f"base {args.name} scaffolded (layout {LAYOUT})",
                agent_subject(args), who)
    print(f"base {args.name}: scaffolded at {root}, registered"
          f"{' as default' if reg.get('default') == args.name else ''}.")


def cmd_adopt(args):
    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        die(f"{root} is not a directory")
    reg = load_registry(args)
    if any(Path(k.get("path", "")).expanduser() == root for k in reg["kbs"]):
        die(f"{root} already registered")
    name = args.name or root.name
    has_baseyaml = (root / "BASE.yaml").exists()
    audience = args.audience
    if has_baseyaml:
        Base(root)  # layout guard first: a mismatched tree must fail BEFORE registering
        cfg = yaml.safe_load((root / "BASE.yaml").read_text(encoding="utf-8")) or {}
        # most-restrictive rule: base-side shared wins over a private claim
        if cfg.get("audience") == "shared":
            audience = "shared"
    entry = {"name": name, "tag": name, "path": str(root), "remote": None,
             "sync": "manual", "audience": audience,
             "methodology": "karpathy-llm-wiki" if has_baseyaml else "none",
             "purpose": (args.purpose or "").strip(),
             "routing": {"channels": [], "keywords": []}}
    reg["kbs"].append(entry)
    reg.setdefault("confidence_bar", 0.7)
    save_registry(args, reg)
    print(f"adopted {name} at {root} (audience: {audience}, sync: manual).")
    print()
    if has_baseyaml:
        args.base = str(root)
        args.write_report = False
        cmd_lint(args)
    else:
        print("divergence: no BASE.yaml — not a kit-native base. Report:")
        for probe, label in [("AGENTS.md", "root contract"), ("index.md", "index"),
                             ("state.yaml", "state file"), ("raw", "raw/ zone")]:
            status = "present" if (root / probe).exists() else "MISSING"
            print(f"  - {label}: {status}")
        print("  convergence path: create BASE.yaml (owner-approved zones/types), "
              "then re-run `kb lint`. Nothing was written into the tree.")


def _do_capture(base: Base, content: str, title: str, source: str, agent: str,
                author: tuple[str, str] | None = None, principal: str = "user",
                quiet: bool = False):
    """Core capture: dedup + frontmatter + commit. Returns dest Path or None (dup)."""
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    cap_dir = base.root / "raw" / "captures"
    cap_dir.mkdir(parents=True, exist_ok=True)
    for p in (base.root / "raw").rglob("*.md"):
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
    slug = slugify(title)
    dst = cap_dir / f"{today()}-{slug}.md"
    n = 2
    while dst.exists():
        dst = cap_dir / f"{today()}-{slug}-{n}.md"
        n += 1
    fm = {"title": title, "type": "capture", "created": today(),
          "timestamp": today(), "source": source,
          "source_sha256": sha,
          "captured_at": now_ts(), "captured_by": principal,
          "triage": "pending", "verified": False}
    write_frontmatter(dst, fm, content if content.endswith("\n") else content + "\n")
    base.commit("capture", dst, f"pending: {title[:50]}", agent, author)
    return dst


def cmd_capture(args):
    base = resolve_base(args)
    if args.file:
        content = Path(args.file).expanduser().read_text(encoding="utf-8")
        title = args.title or Path(args.file).stem
    elif args.text:
        content = args.text
        title = args.title or content.strip().splitlines()[0][:60]
    else:
        content = sys.stdin.read()
        title = args.title or (content.strip().splitlines() or ["capture"])[0][:60]
    if not content.strip():
        die("empty capture")
    agent, author, principal = acting(args, base)
    dst = _do_capture(base, content, title, args.source or "manual",
                      agent, author, principal)
    if dst:
        print(f"captured: {base.rel(dst)} (triage: pending)")


def cmd_inbox(args):
    """The inbox is a view, and by default it is *this principal's* view.

    A base several people share otherwise hands every household's archiver every
    other household's pending captures: the same captures get promoted once per
    household, and one person's raw material lands in another person's agent context
    while that agent holds write access to shared knowledge. `--all` is the
    designated-curator (and CI) path."""
    base = resolve_base(args)
    _, _, principal = acting(args, base)
    want = "failed" if args.failed else "pending"
    found = others = 0
    for p in sorted((base.root / "raw").rglob("*.md")):
        fm, _ = read_frontmatter(p)
        if not fm or fm.get("triage") != want:
            continue
        if not args.all and fm.get("captured_by", "user") != principal:
            others += 1
            continue
        found += 1
        meta = fm.get("meta") if isinstance(fm.get("meta"), dict) else {}
        extra = f"  error: {meta.get('error', '')}" if want == "failed" else ""
        print(f"{base.rel(p)}  [{fm.get('captured_at', '?')}]{extra}")
    print(f"({found} {want} item{'s' if found != 1 else ''})")
    if others:
        # A count, never a path: the point is to say the queue is not empty for
        # someone else, not to show what they captured.
        print(f"({others} more belong to other principals — `--all` to include)")


def cmd_state(args):
    base = resolve_base(args)
    agent, author, principal = acting(args, base)
    st = base.load_state(principal)
    items = st["items"]
    sp = base.state_path(principal)

    def persist(summary: str):
        base.save_state(st, principal)
        base.commit("state", sp, summary, agent, author)

    if args.op == "show":
        if getattr(args, "all", False):
            # The union across shards is the team's current-truth view; each shard
            # still has exactly one writer, which is what keeps it mergeable.
            for p in base.state_paths():
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                print(f"# {base.rel(p)}")
                print(yaml.safe_dump(data, sort_keys=False,
                                     allow_unicode=True).strip())
                print()
            return
        print(yaml.safe_dump(st, sort_keys=False, allow_unicode=True).strip())
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


# -- search / links ------------------------------------------------------

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
    pages = _collect_pages(base)
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


def _link_graph(base: Base):
    """Return (outlinks: rel -> set(rel), known: set of page rel-stems)."""
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
    graph = _link_graph(base)
    if args.orphans:
        inbound = {t for targets in graph.values() for t in targets}
        for rel in sorted(graph):
            if rel not in inbound and not rel.startswith("raw/"):
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


# -- lint ----------------------------------------------------------------

def cmd_lint(args):
    base = resolve_base(args)
    critical, findings, info = [], [], []
    types = set(base.cfg.get("types") or [])
    extensions = set((base.cfg.get("frontmatter") or {}).get("extensions") or [])

    titles_seen, alias_owner = {}, {}
    graph = _link_graph(base)
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
            findings.append(f"{rel}: type {fm.get('type')!r} not in BASE.yaml types")
        unknown = set(fm) - UNIVERSAL_FIELDS - extensions - RAW_FIELDS
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
        stage = fm.get("growth_stage")
        if stage == "seedling":
            try:
                age = (_dt.date.today()
                       - _dt.date.fromisoformat(str(fm.get("created")))).days
                if age > 30:
                    findings.append(f"{rel}: stale seedling ({age}d) — grow or archive")
            except ValueError:
                pass

    for title, rels in titles_seen.items():
        if len(rels) > 1:
            critical.append(f"duplicate title {title!r}: {rels}")

    # broken links + missing-from-index
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

    # raw checks
    for p in (base.root / "raw").rglob("*.md") if (base.root / "raw").is_dir() else []:
        if "AGENTS" in p.name:
            continue
        rel = base.rel(p)
        fm, _ = read_frontmatter(p)
        if fm is None:
            findings.append(f"{rel}: raw file without frontmatter")
            continue
        tri = fm.get("triage")
        if tri not in TRIAGE_STATES:
            findings.append(f"{rel}: triage {tri!r} not in {sorted(TRIAGE_STATES)}")
        if tri == "failed":
            critical.append(f"{rel}: capture in failed state — needs review")
        if "source_sha256" not in fm:
            findings.append(f"{rel}: missing source_sha256 (dedup key)")

    # backups + LFS dodgers
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
            import fnmatch
            if not any(fnmatch.fnmatch(p.name, pat) for pat in lfs_patterns):
                findings.append(f"{base.rel(p)}: large non-text file "
                                f"({p.stat().st_size // 1024}KB) not matching any "
                                f"LFS pattern in .gitattributes")

    # state checks — one file per principal on a shared base, so each is checked
    # separately and each genuinely has one writer.
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
        findings.append("no state file (state.yaml, or state/<principal>.yaml on a "
                        "shared base)")

    # git health — git is the audit substrate, so its condition is a lint subject.
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

    # grants hygiene: via grammar (revocation depends on it)
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

    # grants audit: authorship x grants over recent commits.
    #
    # This is a real check now rather than one deferred to a cross-check that was
    # never built. Every write is its own commit, so nothing is batched under one
    # identity and there is no exemption to make: the *committer* is the acting agent
    # (the subject a grant names) and the *author* is the principal whose knowledge it
    # is. A commit with neither is the finding.
    grants = base.grants()
    roster = base.principals()
    if is_repo(base.root):
        try:
            out = git(base.root, "log", f"--since={args.audit_days} days ago",
                      "--pretty=%H%x1f%an%x1f%ae%x1f%cn%x1f%s", "--name-only").stdout
            sha = committer = None
            skip_commit = False
            for line in out.splitlines():
                if "\x1f" in line:
                    sha, _an, ae, committer, subject = line.split("\x1f", 4)
                    # `bootstrap` scaffolds the tree before any grant row exists.
                    skip_commit = subject.startswith("bootstrap")
                    if subject.startswith("sweep:"):
                        findings.append(
                            f"commit {sha[:8]}: {subject} — swept by sync rather than "
                            f"written through a verb, so no acting subject was "
                            f"recorded. Use `kb commit` after a hand-write")
                    if not skip_commit and roster and ae.strip().lower() not in roster:
                        findings.append(
                            f"unattributed commit {sha[:8]}: author {ae!r} is not in "
                            f"the BASE.yaml principals roster")
                    continue
                if not line.strip() or skip_commit or not grants:
                    continue
                path = line.strip()
                if path.startswith(".base/"):
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

    # §4.5 layer 2: no LLM-routed write may ever reach a shared base. The exclusion is
    # a list filter, not a threshold, so the check is an existence test — and it is
    # the falsifiable half of the rule the route skill states in prose.
    bar = float((load_registry(args) or {}).get("confidence_bar", 0.7) or 0.7)
    for p in (base.root / "raw").rglob("*.md") if (base.root / "raw").is_dir() else []:
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

    if getattr(args, "write_report", False):
        week = _dt.date.today().isocalendar()
        dst = base.root / "_ops" / f"lint-report-{week[0]}-{week[1]:02d}.md"
        dst.parent.mkdir(exist_ok=True)
        dst.write_text(report, encoding="utf-8")
        agent, author, _ = acting(args, base)
        base.commit("lint", dst, f"{len(critical)} critical, {len(findings)} findings",
                    agent, author)
    # Report-only by default: the report is the interface, and the exit code carries no
    # verdict. `--ci` is the one exception, and it outlived the CI janitor it was built
    # for: a user wiring lint into their own hook or Action needs an exit code, and the
    # alternative is parsing the report text. The default staying report-only is the
    # contract; --ci is what makes that contract falsifiable rather than a preference.
    if getattr(args, "ci", False) and critical:
        sys.exit(1)


def cmd_grants(args):
    base = resolve_base(args)
    ok = base.grant_check(args.subject, args.verb, args.path)
    print(f"{'GRANTED' if ok else 'DENIED'}: {args.subject} {args.verb} {args.path}")
    sys.exit(0 if ok else 1)


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


def cmd_sync(args):
    reg = load_registry(args)
    if args.all:
        targets = [k for k in reg["kbs"] if k.get("sync") == "rebase-5min"]
        # Bases the scheduled sweep does not cover are reported, not dropped: an
        # adopted base is always `manual`, so silence here reads as "everything is
        # synced" when nothing was even looked at.
        for k in reg["kbs"]:
            if k.get("sync") != "rebase-5min":
                print(f"{k.get('name')}: skipped (sync: {k.get('sync')})")
    else:
        base = resolve_base(args)
        targets = [{"name": base.cfg.get("name", base.root.name),
                    "path": str(base.root)}]
    agent = agent_subject(args)
    worst = 0
    for kb in targets:
        root = Path(kb["path"]).expanduser()
        if not is_repo(root):
            print(f"{kb.get('name')}: skipped (not a git repo)")
            continue
        code = _sync_one(root, kb.get("name", root.name), agent,
                         author_identity(args, root))
        worst = max(worst, code)
    sys.exit(worst)


def _remote_ref_missing(proc) -> bool:
    s = (proc.stderr or "").lower()
    return "couldn't find remote ref" in s or "no such ref" in s


def _sync_one(root: Path, name: str, agent: str = "agent:main",
              author: tuple[str, str] | None = None, attempts: int = 3) -> int:
    # Never touch a worktree that is mid-operation. `git add -A` here would stage the
    # conflict-marker versions and commit them, and git then refuses to start another
    # operation over the leftover state — so every later tick fails too, silently,
    # forever. Checking first turns that into one loud, recoverable message.
    seq = sequencer_state(root)
    if seq:
        print(f"{name}: git is mid-{seq} — refusing to sync until that is resolved "
              f"(`git {'rebase' if 'rebase' in seq else 'merge'} --abort`)",
              file=sys.stderr)
        return 5

    base = Base(root, check_layout=False) if (root / "BASE.yaml").exists() else None

    # Sweep anything written outside a tool verb — an agent editing a wiki page by
    # hand. Data safety comes first, so it is committed rather than refused, but the
    # `sweep:` subject marks it as unattributed so lint reports it instead of letting
    # it pass as an ordinary attributed write.
    git(root, "add", "-A")
    if git(root, "diff", "--cached", "--quiet").returncode != 0:
        n = len(git(root, "diff", "--cached", "--name-only").stdout.splitlines())
        env = dict(os.environ)
        env["GIT_COMMITTER_NAME"] = agent
        env["GIT_COMMITTER_EMAIL"] = agent_email(agent)
        env["GIT_AUTHOR_NAME"], env["GIT_AUTHOR_EMAIL"] = (
            author if author and all(author) else (agent, agent_email(agent)))
        r = subprocess.run(
            ["git", "commit", "-q", "-m",
             f"sweep: {n} path{'s' if n != 1 else ''} written outside a verb"],
            cwd=root, capture_output=True, text=True, check=False, env=env)
        if r.returncode:
            print(f"{name}: commit failed", file=sys.stderr)
            return 2

    if git(root, "remote", "get-url", "origin").returncode != 0:
        print(f"{name}: synced (no remote)")
        return 0

    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for attempt in range(1, attempts + 1):
        # Fast-forward where possible; only genuinely diverged history needs a merge.
        # Rebase is deliberately not the default: it rewrites commits another machine
        # may already hold, and a conflicted rebase leaves state that blocks every
        # later tick. Both tools that run unattended across many machines — Obsidian
        # Git and git-annex — made the same call. A braided history nobody reads is a
        # cheaper price than a sync loop that stalls.
        pull = git(root, "pull", "--no-stat", "--ff-only", "origin", branch)
        if pull.returncode != 0 and not _remote_ref_missing(pull):
            pull = git(root, "pull", "--no-stat", "--no-rebase", "--no-edit",
                       "origin", branch)
        if pull.returncode != 0 and not _remote_ref_missing(pull):
            git(root, "merge", "--abort")
            if base:
                entry = base.review(
                    f"sync conflict ({name})",
                    "`git pull` hit a conflict and was aborted cleanly. The base is "
                    "consistent but behind its remote — resolve by hand, then push.",
                    agent)
                base.commit("sync-conflict", entry,
                            f"{name}: pull aborted, needs a human", agent, author)
            print(f"{name}: sync conflict — aborted clean, surfaced to review queue",
                  file=sys.stderr)
            return 3
        if git(root, "push", "-q", "origin", branch).returncode == 0:
            print(f"{name}: synced")
            return 0
        # Lost the push race — someone pushed between our pull and our push. With
        # several machines on one interval the ticks land on the same wall-clock
        # second, so this is systematic rather than rare; jittered backoff is what
        # breaks the lockstep.
        if attempt < attempts:
            time.sleep(min(2 ** attempt, 8) + random.random())
    print(f"{name}: push failed after {attempts} attempts", file=sys.stderr)
    return 4


def cmd_refuse(args):
    """Record a refused write: a `refuse` commit plus a review-queue entry ([D] per
    kb-authorization §3.1). The payload stays with the caller — this only records.
    A refusal is one of the events git could not otherwise hold, since by definition
    nothing else changed; the queue entry is what gives it a file to commit."""
    base = resolve_base(args)
    agent, author, _ = acting(args, base)
    entry = base.review(
        f"refused write — {args.path}",
        f"Subject `{args.subject or agent}` was refused `{args.verb}` on "
        f"`{args.path}`: {args.reason or 'no grant'}. The payload stays with the "
        f"caller; install the capability properly (grants via the diff gate) or "
        f"dismiss.", agent)
    base.commit("refuse", entry, (args.reason or "no grant")[:120], agent, author)
    print(f"refusal recorded: {args.path}")


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


# -- import survey (design §6.7) -----------------------------------------
# Import itself is an AGENT procedure (the import skill) — transform-on-import
# means every page passes through agent judgment, so there is no apply engine.
# The tool contributes exactly one deterministic piece: the survey (inventory +
# shape detection), so the agent never burns a context walking a big tree.
# The source is READ-ONLY, always.

IMPORT_SKIP_DEFAULT = ["**/.git/**", "**/.obsidian/**", "**/node_modules/**",
                       "**/.base/**", "**/*.backup.*", "**/*.bak"]


def _src_files(src: Path, skips):
    import fnmatch
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src).as_posix()
        if any(fnmatch.fnmatch(rel, s) or fnmatch.fnmatch("/" + rel, s)
               for s in skips):
            continue
        yield rel, p


def cmd_import_survey(args):
    src = Path(args.src).expanduser().resolve()
    if not src.is_dir():
        die(f"{src} is not a directory")
    # shape detection
    if (src / "BASE.yaml").exists():
        shape = "base-v2"
    elif (src / "SCHEMA.md").exists() and ((src / "state").is_dir()
                                           or (src / "ops" / "inbox.md").exists()):
        shape = "old-methodology"
    elif (src / ".obsidian").is_dir():
        shape = "obsidian"
    else:
        shape = "plain"

    by_dir, by_ext, fm_fields = {}, {}, {}
    links = md = big = 0
    big_files = []
    for rel, p in _src_files(src, IMPORT_SKIP_DEFAULT):
        top = rel.split("/")[0] if "/" in rel else "."
        by_dir[top] = by_dir.get(top, 0) + 1
        ext = p.suffix or "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1
        if p.suffix == ".md":
            md += 1
            fm, body = read_frontmatter(p)
            for k in (fm or {}):
                fm_fields[k] = fm_fields.get(k, 0) + 1
            links += len(WIKILINK_RE.findall(body))
        elif p.stat().st_size > 1024 * 1024:
            big += 1
            big_files.append(rel)

    if args.json:
        print(json.dumps({"shape": shape, "by_dir": by_dir, "by_ext": by_ext,
                          "md_files": md, "wikilinks": links,
                          "frontmatter_fields": fm_fields,
                          "large_binaries": big_files}, indent=2))
        return
    print(f"# import survey — {src}\n")
    print(f"shape: {shape}"
          + ("  (has BASE.yaml — use `kb adopt`, not import)"
             if shape == "base-v2" else ""))
    print(f"markdown files: {md} · wikilinks: {links} · large binaries: {big}")
    print("\nby top-level dir:")
    for d, n in sorted(by_dir.items(), key=lambda x: -x[1]):
        print(f"  {d:24} {n}")
    print("\nfrontmatter fields seen (count):")
    for k, n in sorted(fm_fields.items(), key=lambda x: -x[1]):
        print(f"  {k:24} {n}")
    if big_files:
        print("\nlarge binaries (candidates for LFS-tracked attachment sets):")
        for rel in big_files[:20]:
            print(f"  {rel}")


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


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        prog="kb",
        description="Deterministic executor for kb bases. Judgment-free: skills "
                    "decide, this tool does. See `--help` per verb.")
    ap.add_argument("--version", action="version", version=f"kb {VERSION} "
                    f"(layout {LAYOUT})")
    ap.add_argument("--base", help="base name (registry) or path; default: cwd/"
                    "registry default")
    ap.add_argument("--registry", help="kb-registry.yaml path (default: <home>/personal/kb-registry.yaml)")
    ap.add_argument("--agent", help="acting subject — the committer of every write "
                    "(default $AOS_AGENT or agent:main)")
    ap.add_argument("--author-name", help="the human principal a write belongs to; "
                    "becomes the git author (default $AOS_PRINCIPAL_NAME, else the "
                    "repo's own git identity)")
    ap.add_argument("--author-email", help="that principal's email — what the "
                    "BASE.yaml principals roster keys on (default "
                    "$AOS_PRINCIPAL_EMAIL, else the repo's git identity)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="scaffold + register a new base")
    p.add_argument("name")
    p.add_argument("--path", required=True)
    p.add_argument("--audience", choices=["private", "shared"], default="private")
    p.add_argument("--purpose", default="")
    p.add_argument("--sync", choices=["rebase-5min", "manual", "none"],
                   default="manual")
    p.add_argument("--remote")
    p.add_argument("--tag")
    p.add_argument("--default", action="store_true")
    p.add_argument("--templates")
    p.add_argument("--kb-version", default=VERSION)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("adopt", help="register an existing tree; report divergence; "
                       "zero writes into it")
    p.add_argument("path")
    p.add_argument("--name")
    p.add_argument("--audience", choices=["private", "shared"], default="private")
    p.add_argument("--purpose", default="")
    p.add_argument("--audit-days", type=int, default=8)
    p.set_defaults(func=cmd_adopt)

    p = sub.add_parser("capture", help="instant mechanical capture into raw/captures/")
    p.add_argument("--text")
    p.add_argument("--file")
    p.add_argument("--title")
    p.add_argument("--source", help="channel provenance, e.g. whatsapp:voice")
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("inbox", help="the inbox is a view: this principal's pending "
                       "items (--all for everyone's)")
    p.add_argument("--failed", action="store_true")
    p.add_argument("--all", action="store_true",
                   help="include other principals' items (designated-curator and CI "
                        "path); default is yours alone")
    p.set_defaults(func=cmd_inbox)

    p = sub.add_parser("state", help="attention-window ops (capped)")
    p.add_argument("op", choices=["add", "bump", "drop", "check", "show"])
    p.add_argument("--note")
    p.add_argument("--ref")
    p.add_argument("--review-by")
    p.add_argument("--stale-days", type=int, default=42)
    p.add_argument("--all", action="store_true",
                   help="show: the union across every principal's shard")
    p.set_defaults(func=cmd_state)

    p = sub.add_parser("search", help="BM25 over the base; exact/alias hits first "
                       "with a create-safety verdict")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("links", help="backlinks / outbound / orphans")
    p.add_argument("page", nargs="?")
    p.add_argument("--orphans", action="store_true")
    p.set_defaults(func=cmd_links)

    p = sub.add_parser("lint", help="the deterministic check catalog (report-only; "
                       "the report is the interface)")
    p.add_argument("--write-report", action="store_true")
    p.add_argument("--audit-days", type=int, default=8)
    p.add_argument("--ci", action="store_true",
                   help="exit 1 on any critical — for a hook or an unattended runner "
                        "that needs a verdict rather than a report")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("grants", help="grant lookup")
    p.add_argument("check", choices=["check"])
    p.add_argument("--subject", required=True)
    p.add_argument("--verb", required=True)
    p.add_argument("--path", required=True)
    p.set_defaults(func=cmd_grants)

    p = sub.add_parser("index", help="regenerate index.md from the tree")
    p.add_argument("rebuild", choices=["rebuild"])
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("sync", help="ff-pull then merge on divergence, push with "
                       "jittered retry; conflict -> safe abort + review entry + "
                       "exit 3; never calls an LLM")
    p.add_argument("--all", action="store_true",
                   help="every registry base with sync: rebase-5min (the rest are "
                        "reported as skipped, never silently dropped)")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("commit", help="attribute a hand-written change (author = "
                       "principal, committer = agent, aos-verb trailer)")
    p.add_argument("--verb", required=True, help="one of the aos-verb vocabulary")
    p.add_argument("--path", required=True, action="append",
                   help="repeatable; base-relative")
    p.add_argument("--summary", required=True)
    p.set_defaults(func=cmd_commit)

    p = sub.add_parser("history", help="recent activity from git — the orientation "
                       "read, in a pinned format")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("refuse", help="record a refused write (refuse commit + "
                       "review-queue entry); payload stays with the caller")
    p.add_argument("--path", required=True)
    p.add_argument("--verb", default="write")
    p.add_argument("--subject")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_refuse)

    p = sub.add_parser("verify", help="flip a page to verified: true (user-confirmed)")
    p.add_argument("page")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("import", help="bulk import of a foreign KB (source is "
                       "READ-ONLY, always; design §6.7)")
    imp = p.add_subparsers(dest="import_cmd", required=True)
    ps = imp.add_parser("survey", help="inventory + shape detection of a source tree")
    ps.add_argument("src")
    ps.add_argument("--json", action="store_true")
    ps.set_defaults(func=cmd_import_survey)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
