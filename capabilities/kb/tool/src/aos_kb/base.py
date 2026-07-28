"""`Base` — one kb base on disk, layout-checked. `resolve_base()` finds the one a verb
is acting on; `acting()` is the (agent, author, grants-subject) triple every write
verb needs.

Moved verbatim from cli.py; no behavior change and no signature change yet — the
argparse `Namespace`-shaped `args` parameter stays exactly as-is here. The typer
callback rewrite (a later task) is what changes what `resolve_base`/`acting` receive.
"""

import datetime as _dt
import os
import subprocess
from pathlib import Path
from typing import NamedTuple

import yaml

from .constants import LAYOUT, AOS_VERBS, PENDING_KINDS, WAITS_ON
from .frontmatter import slugify, write_frontmatter, glob_to_re
from .identity import (
    today, die, agent_email, is_repo, agent_subject, resolve_principal,
    principal_name,
)
from .registry import load_registry


class GrantRow(NamedTuple):
    """One row of AGENTS.md's '## Grants' table: who (subject), on what
    (object — a space-separated set of git-style globs), doing which verbs."""
    subject: str
    object: str
    verbs: list[str]


class Base:
    """One base on disk, layout-checked."""

    def __init__(self, root: Path, check_layout: bool = True):
        self.root = root.resolve()
        cfg_path = self.root / ".kb" / "base.yml"
        if not cfg_path.exists():
            # Recognise the old tree so the message is a pointer, not a guess.
            if (self.root / "BASE.yaml").exists():
                die(f"{self.root} is a layout 1 base (root BASE.yaml). This tool "
                    f"speaks layout {LAYOUT} — run `kb migrate --base {self.root}`. "
                    f"Refusing to guess at paths.", 11)
            die(f"{self.root} has no .kb/base.yml — not a base (adopt it first?)", 10)
        self.cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        if check_layout:
            layout = self.cfg.get("layout")
            if layout != LAYOUT:
                die(f"{self.root}: base.yml layout={layout!r}, this tool speaks "
                    f"layout={LAYOUT}. Refusing to guess — run `kb migrate`.", 11)

    # -- .kb/ — three subdirectories, three tests: waiting on someone · in progress ·
    # rebuildable. Anything that fits none of the three does not belong under .kb/.
    @property
    def kb_dir(self) -> Path:
        return self.root / ".kb"

    @property
    def pending_dir(self) -> Path:
        return self.kb_dir / "pending"

    @property
    def work_dir(self) -> Path:
        return self.kb_dir / "work"

    @property
    def cache_dir(self) -> Path:
        return self.kb_dir / "cache"

    @property
    def raw_dir(self) -> Path:
        return self.root / "_raw"

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

    def curation(self) -> str:
        """`self` (default) or `designated`. A mode the grants table already expressed:
        under `self` everyone holds capture + propose grants and drains only their own;
        under `designated` one principal holds the wiki write grants and reads
        everyone's raw material. Rule of two — a third mode earns a richer field."""
        return str(self.cfg.get("curation") or "self").strip()

    def curator(self) -> str:
        return str(self.cfg.get("curator") or "").strip().lower()

    def is_curator(self, pid: str) -> bool:
        return (self.curation() == "designated"
                and bool(self.curator())
                and (pid or "").strip().lower() == self.curator())

    def grant_subject(self, pid: str) -> str:
        """The grants table names principal ids directly, so it IS the roster. A base
        with no row for this id falls back to `user` — the single-human case, which is
        every private base and needs no configuration at all."""
        pid = (pid or "").strip().lower()
        for row in self.grants():
            if row.subject.strip().lower() == pid:
                return row.subject
        return "user"

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

    def pending_add(self, kind: str, waits_on: str, title: str, body: str,
                    agent: str = "", extra: dict = None) -> Path:
        """One file per pending item. A single appended queue file is written by every
        agent on every machine, which is precisely the shape that conflicts on every
        sync; distinct filenames never do. The queue is a view over the directory.

        There is no `status:` field: an entry in the directory is open, and resolving it
        removes the file. Location is the state here too."""
        if kind not in PENDING_KINDS:
            die(f"unknown kind {kind!r} — the closed set is "
                f"{' '.join(sorted(PENDING_KINDS))}")
        if waits_on not in WAITS_ON:
            die(f"unknown --waits-on {waits_on!r} — the closed set is "
                f"{' '.join(sorted(WAITS_ON))}")
        d = self.pending_dir
        d.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
        slug = slugify(title)
        dst = d / f"{stamp}-{slug}.md"
        n = 2
        while dst.exists():
            dst = d / f"{stamp}-{slug}-{n}.md"
            n += 1
        fm = {"title": title, "kind": kind, "waits_on": waits_on,
              "created": today(), "raised_by": agent or "unknown"}
        fm.update(extra or {})
        write_frontmatter(dst, fm, body if body.endswith("\n") else body + "\n")
        return dst

    # -- state -------------------------------------------------------------
    def state_path(self, principal: str | None = None) -> Path:
        """One shard per principal, ALWAYS — never conditional on audience. The rolling
        attention window is one person's by nature, and a single file rewritten in place
        by everyone is the one shape git cannot merge. Sharding makes methodology §7's
        single writer literally true, while "the team's current-truth" survives as the
        union of the shards. The old private-base special case was a second code path
        that only the shared case ever exercised."""
        return self.kb_dir / "state" / f"{slugify(principal or 'user')}.yml"

    def state_paths(self) -> list[Path]:
        """Every state file in the base — the union view."""
        d = self.kb_dir / "state"
        return sorted(d.glob("*.yml")) if d.is_dir() else []

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
                  ".kb/base.yml state.max_items; git history is the archive.\n")
        p = self.state_path(principal)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(header + yaml.safe_dump(data, sort_keys=False,
                                             allow_unicode=True), encoding="utf-8")

    def state_cap(self) -> int:
        return int((self.cfg.get("state") or {}).get("max_items", 20))

    # -- grants ------------------------------------------------------------
    def grants(self) -> list[GrantRow]:
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
                    rows.append(GrantRow(subject=cells[0], object=cells[1],
                                         verbs=cells[2].split()))
            elif in_table and line.strip():
                break
        return rows

    def grant_check(self, subject: str, verb: str, path: str) -> bool:
        rows = self.grants()
        # `*` means "any REGISTERED subject", and registration is having a row of your
        # own — that is the only definition the table can support, since the table IS
        # the roster. The previous test was `subject != "(unregistered)"`, a magic
        # string nothing ever produces, so every unknown subject matched `*` and the
        # documented "an unregistered subject matches nothing, not even `*`" was
        # unimplemented: `grants check --subject eve@evil.example --verb read` returned
        # GRANTED on any base carrying the default `* ** read` row.
        registered = any(r.subject == subject for r in rows)
        for row in rows:
            subj_ok = row.subject == subject or (row.subject == "*" and registered)
            if not subj_ok or verb not in row.verbs:
                continue
            for pat in row.object.split():
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
        if (p / ".kb" / "base.yml").exists():
            return Base(p)
    reg = load_registry(args)
    default = reg.get("default")
    for kb in reg["kbs"]:
        if kb.get("name") == default:
            return Base(Path(kb["path"]).expanduser())
    die("no base: pass --base <name|path>, cd into one, or set a registry default")


def acting(args, base: Base) -> tuple[str, tuple[str, str], str]:
    """(agent subject, git author identity, grants subject) for this invocation.

    The agent is the committer and the principal is the git author. The grants subject
    is the principal id itself when the table names it, else `user` — the single-human
    case, which is every private base."""
    agent = agent_subject(args)
    pid = resolve_principal(args, base.cfg.get("name", base.root.name), base.root)
    author = (principal_name(args, base.root, pid), pid)
    return agent, author, base.grant_subject(pid)
