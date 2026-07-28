"""The three verbs that create or convert a base's on-disk identity: `init`
scaffolds one, `adopt` registers an existing tree, `migrate` carries a LAYOUT 1 base
to LAYOUT 2. Grouped together because each shares the "does this tree already have a
.kb/base.yml?" question at the top, and `migrate` deliberately shadows the global
`--base` (the shared one resolves through `Base()`, which refuses a layout 1 tree by
design — migrate is the one verb that must accept one)."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated, Literal, Optional

import typer
import yaml

from ..constants import VERSION, LAYOUT, TEMPLATE_REPO_URL
from ..frontmatter import slugify, read_frontmatter, write_frontmatter
from ..identity import (
    today, die, agent_subject, is_repo, git, is_weak_principal, principal_file,
    resolve_principal, principal_name,
)
from ..registry import load_registry, save_registry, find_upstream_root
from ..base import Base, acting
# cmd_adopt calls into lint's report-generation logic directly, as a plain function
# with explicit keyword defaults for the flags adopt's own subparser never declared
# (stale_pending_days, ci) — not an attempt to invoke a wrapped typer Command object
# programmatically. No import cycle: lint.py imports from wiki.py, never lifecycle.py.
from .lint import _run_lint

app = typer.Typer()


def _resolve_templates(templates: Optional[str], template_repo: str,
                       tmp_holder: list) -> Path:
    """Where init's templates come from: --templates (a local dir — skip the network
    step entirely, unchanged from before this repo existed) beats a clone of
    --template/the default TEMPLATE_REPO_URL, which falls back to the tree shipped
    inside this checkout on any clone failure (no network, bad URL, git not configured
    for the host, ...). The fallback is silent-but-noted, never blocking or prompting —
    the same shape as the `git lfs version` check just below in cmd_init.

    `tmp_holder` is a one-element list the caller appends the TemporaryDirectory to
    (if a clone happened), so it can be cleaned up only after every render() call that
    reads out of it has run — a `with` block here would tear it down too soon."""
    if templates:
        return Path(templates).expanduser()
    tmp = tempfile.TemporaryDirectory()
    dst = Path(tmp.name) / "template"
    r = subprocess.run(["git", "clone", "-q", "--depth", "1", template_repo, str(dst)],
                       capture_output=True, text=True, check=False)
    if r.returncode == 0 and (dst / "base.yml").exists():
        shutil.rmtree(dst / ".git", ignore_errors=True)
        tmp_holder.append(tmp)   # keep the TemporaryDirectory alive past this call
        return dst
    tmp.cleanup()
    print(f"note: couldn't clone the template repo ({template_repo}) — "
          f"falling back to the templates shipped in this checkout "
          f"(`git lfs version`-style degrade: never blocks, never prompts).")
    return find_upstream_root() / "capabilities" / "kb" / "skills" / "init" / "templates"


@app.command("init", help="scaffold + register a new base")
def cmd_init(
    ctx: typer.Context,
    name: str,
    path: Annotated[str, typer.Option()],
    audience: Literal["private", "shared"] = "private",
    purpose: str = "",
    sync: Literal["rebase-5min", "manual", "none"] = "manual",
    remote: Optional[str] = None,
    tag: Optional[str] = None,
    default: bool = False,
    templates: Annotated[Optional[str], typer.Option(
        help="a local template directory — skips the network step entirely")] = None,
    template: Annotated[str, typer.Option(
        help="template repo to clone (git URL or local path); "
             "ignored if --templates is given")] = TEMPLATE_REPO_URL,
    kb_version: str = VERSION,
    curation: Annotated[Literal["self", "designated"], typer.Option(
        help="self: everyone drains their own queue (default). designated: one "
             "principal holds the wiki write grants and reads everyone's raw "
             "material — name them with --curator")] = "self",
    curator: Annotated[Optional[str], typer.Option(
        help="principal id, iff --curation designated")] = None,
):
    root = Path(path).expanduser().resolve()
    if (root / ".kb" / "base.yml").exists():
        die(f"{root} already has a .kb/base.yml")
    tmp_holder = []
    tpl = _resolve_templates(templates, template, tmp_holder)
    if not (tpl / "base.yml").exists():
        die(f"templates not found at {tpl} (pass --templates)")
    root.mkdir(parents=True, exist_ok=True)

    subs = {"{{name}}": name, "{{today}}": today(),
            "{{version}}": kb_version, "{{audience}}": audience,
            "{{purpose}}": (purpose or "").strip(),
            "{{sync_mode}}": sync,
            "{{curation}}": curation,          # self | designated
            "{{curator}}": curator or ""}      # principal id, iff designated

    rendered = []

    def render(src: Path, dst: Path):
        text = src.read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(k, v)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        rendered.append(dst)

    render(tpl / "base.yml", root / ".kb" / "base.yml")
    for tname in ["AGENTS.md", "index.md"]:
        render(tpl / tname, root / tname)

    base = Base(root)
    pid = resolve_principal(ctx.obj, name, root)
    render(tpl / "state.yml", base.state_path(pid))

    for zone, d in base.zones().items():
        (root / zone).mkdir(exist_ok=True)
        zone_tpl = tpl / "zones" / f"{zone}.AGENTS.md"
        if zone_tpl.exists():
            render(zone_tpl, root / zone / "AGENTS.md")
        for sub in (d or {}).get("subdirs", []) if isinstance(d, dict) else []:
            (root / zone / sub).mkdir(exist_ok=True)
    for d in (base.pending_dir, base.work_dir, base.cache_dir, base.raw_dir):
        d.mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text(".kb/cache/\n", encoding="utf-8")
    if (tpl / "gitattributes").exists():
        render(tpl / "gitattributes", root / ".gitattributes")

    # A missing substitution is silent otherwise, and an unrendered {{curation}} in a
    # committed base.yml is a parse error waiting to happen.
    for p in rendered:
        if "{{" in p.read_text(encoding="utf-8"):
            die(f"{base.rel(p)}: unrendered placeholder left after templating — "
                f"a template introduced a variable this tool does not substitute", 14)

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
    if is_weak_principal(pid):
        print(f"note: writes will be authored by {pid!r}, a synthesized identity — "
              f"`kb lint` reports it. Fix it in {principal_file()}, or let kb's "
              f"onboarding interview ask.")
    if remote:
        subprocess.run(["git", "remote", "add", "origin", remote],
                       cwd=root, check=False)

    reg = load_registry(ctx.obj)
    existing = next((k for k in reg["kbs"] if k.get("name") == name), None)
    if existing:
        # A pre-seeded registry entry (interview ran first) is fine iff it points at
        # this path and the tree doesn't exist yet — init fills it in. Anything else
        # is a genuine duplicate.
        if Path(existing.get("path", "")).expanduser().resolve() != root:
            die(f"base {name!r} already registered at a different path")
        existing.setdefault("tag", tag or name)
        if (purpose or "").strip():
            existing["purpose"] = purpose.strip()
    else:
        entry = {"name": name, "tag": tag or name,
                 "path": str(root), "remote": remote,
                 "sync": sync, "audience": audience,
                 # No methodology: field — the seam dissolved (kb IS the methodology),
                 # so the line wrote a value with no reader.
                 "purpose": (purpose or "").strip(),
                 "routing": {"channels": [], "keywords": []}}
        reg["kbs"].append(entry)
    if default or not reg.get("default"):
        reg["default"] = name
    reg.setdefault("confidence_bar", 0.7)
    save_registry(ctx.obj, reg)

    base.commit("bootstrap", ".", f"base {name} scaffolded (layout {LAYOUT})",
                agent_subject(ctx.obj), (principal_name(ctx.obj, root, pid), pid))
    print(f"base {name}: scaffolded at {root}, registered"
          f"{' as default' if reg.get('default') == name else ''}.")
    for tmp in tmp_holder:      # the cloned template's TemporaryDirectory, if any
        tmp.cleanup()


@app.command("adopt", help="register an existing tree; report divergence; zero "
                          "writes into it")
def cmd_adopt(
    ctx: typer.Context,
    path: str,
    name: Optional[str] = None,
    audience: Literal["private", "shared"] = "private",
    purpose: str = "",
    audit_days: int = 8,
):
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        die(f"{root} is not a directory")
    reg = load_registry(ctx.obj)
    if any(Path(k.get("path", "")).expanduser() == root for k in reg["kbs"]):
        die(f"{root} already registered")
    name = name or root.name
    has_cfg = (root / ".kb" / "base.yml").exists()
    if has_cfg:
        Base(root)  # layout guard first: a mismatched tree must fail BEFORE registering
        cfg = yaml.safe_load(
            (root / ".kb" / "base.yml").read_text(encoding="utf-8")) or {}
        # most-restrictive rule: base-side shared wins over a private claim
        if cfg.get("audience") == "shared":
            audience = "shared"
    entry = {"name": name, "tag": name, "path": str(root), "remote": None,
             "sync": "manual", "audience": audience,
             "purpose": (purpose or "").strip(),
             "routing": {"channels": [], "keywords": []}}
    reg["kbs"].append(entry)
    reg.setdefault("confidence_bar", 0.7)
    save_registry(ctx.obj, reg)
    print(f"adopted {name} at {root} (audience: {audience}, sync: manual).")
    print()
    if has_cfg:
        # `_run_lint` supplies real defaults for stale_pending_days/ci here —
        # neither was ever a flag on this subparser under argparse, and reading
        # them unconditionally (cli.py:1414's old bare `args.stale_pending_days`)
        # crashed with AttributeError on a base carrying an aged human-waits
        # pending item. Explicit keyword defaults close that gap deliberately.
        adopted_base = Base(root)
        _run_lint(adopted_base, ctx.obj, write_report=False, audit_days=audit_days)
    else:
        print("divergence: no .kb/base.yml — not a kit-native base. Report:")
        for probe, label in [("AGENTS.md", "root contract"), ("index.md", "index"),
                             (".kb/state", "state shards"), ("_raw", "_raw/ zone")]:
            status = "present" if (root / probe).exists() else "MISSING"
            print(f"  - {label}: {status}")
        print("  convergence path: create .kb/base.yml (owner-approved zones/types), "
              "then re-run `kb lint`. Nothing was written into the tree.")


@app.command("migrate", help="carry a layout 1 base to layout 2 (git mv throughout, "
                            "so history follows)")
def cmd_migrate(
    ctx: typer.Context,
    # Its own --base, deliberately: the global one resolves through Base(), which
    # refuses a layout 1 tree by design. Migrate is the one verb that must accept one.
    base: Annotated[Optional[str], typer.Option(
        help="the layout 1 base to carry across (default: cwd)")] = None,
):
    """LAYOUT 1 -> 2, with `git mv` for every move so history follows. Refuses a dirty
    worktree: a migration that mixes with uncommitted work cannot be reverted cleanly,
    and revert is the only undo this has."""
    root = Path(base or getattr(ctx.obj, "base", None)
                or ".").expanduser().resolve()
    if (root / ".kb" / "base.yml").exists():
        print(f"{root}: already layout 2 — nothing to do.")
        return
    if not (root / "BASE.yaml").exists():
        die(f"{root} is not a base (no BASE.yaml, no .kb/base.yml)", 10)
    if is_repo(root) and git(root, "status", "--porcelain").stdout.strip():
        die("uncommitted changes — commit or stash first. A migration that mixes "
            "with uncommitted work cannot be reverted cleanly.", 13)

    cfg = yaml.safe_load((root / "BASE.yaml").read_text(encoding="utf-8")) or {}
    moved, dropped = [], []

    def mv(src: str, dst: str):
        s_path = root / src
        if not s_path.exists():
            return False
        (root / dst).parent.mkdir(parents=True, exist_ok=True)
        if is_repo(root) and git(root, "mv", src, dst).returncode == 0:
            moved.append(f"{src} -> {dst}")
            return True
        s_path.rename(root / dst)
        moved.append(f"{src} -> {dst}")
        return True

    def rm(rel: str):
        p = root / rel
        if not p.exists():
            return
        if not (is_repo(root) and git(root, "rm", "-r", "-q", "--", rel).returncode == 0):
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink()
        dropped.append(rel)

    # 1. the config, then rewritten in place below
    mv("BASE.yaml", ".kb/base.yml")

    # 2. state -> one shard per principal. The old flat file is this principal's by
    #    definition: a layout 1 private base had exactly one writer.
    pid = resolve_principal(ctx.obj, cfg.get("name", root.name), root)
    if (root / "state.yaml").exists():
        mv("state.yaml", f".kb/state/{slugify(pid)}.yml")
    old_shards = root / "state"
    if old_shards.is_dir():
        for shard in sorted(old_shards.glob("*.yaml")):
            mv(f"state/{shard.name}", f".kb/state/{shard.stem}.yml")

    # 3. raw/ -> _raw/ flat, and triage: becomes location. A pending capture goes to
    #    .kb/pending/ instead, because that is now what "pending" means.
    old_raw = root / "raw"
    if old_raw.is_dir():
        for p in sorted(old_raw.rglob("*.md")):
            rel = p.relative_to(root).as_posix()
            if "AGENTS" in p.name:
                rm(rel)                       # the zone contract is re-rendered, not moved
                continue
            fm, body = read_frontmatter(p)
            triage = str((fm or {}).get("triage", "done"))
            dst_dir = ".kb/pending" if triage == "pending" else "_raw"
            dst = f"{dst_dir}/{p.name}"
            n = 2
            while (root / dst).exists():
                dst = f"{dst_dir}/{p.stem}-{n}.md"
                n += 1
            if not mv(rel, dst):
                continue
            if fm is None:
                continue
            fm.pop("triage", None)
            if triage == "pending":
                # The queue's own fields, added on the way in.
                fm = {"title": fm.get("title", p.stem), "kind": "capture",
                      "waits_on": "agent",
                      **{k: v for k, v in fm.items() if k != "title"}}
            elif triage == "failed":
                fm["failed"] = "carried over from layout 1 triage: failed"
            write_frontmatter(root / dst, fm, body)
        rm("raw")

    # 4. the review queue -> .kb/pending/, with the kind read off the old title
    old_q = root / "_ops" / "needs-review"
    if old_q.is_dir():
        for p in sorted(old_q.glob("*.md")):
            rel = p.relative_to(root).as_posix()
            fm, body = read_frontmatter(p)
            title = str((fm or {}).get("title", p.stem))
            low = title.lower()
            kind = ("refusal" if "refus" in low else
                    "conflict" if "conflict" in low else
                    "entity" if "entit" in low or "mention" in low else "finding")
            dst = f".kb/pending/{p.name}"
            if not mv(rel, dst):
                continue
            fm = fm or {"title": title}
            fm.pop("status", None)            # in the directory IS open
            fm = {"title": title, "kind": kind, "waits_on": "human",
                  **{k: v for k, v in fm.items() if k != "title"}}
            write_frontmatter(root / dst, fm, body)

    # 5. import working files -> .kb/work/
    for iname in ("import-agreement.md", "import-progress.md"):
        mv(f"_ops/{iname}", f".kb/work/{iname}")

    # 6. what does not come forward. _archive/ is git rm'd rather than copied: the
    #    history IS the archive, which is the whole argument for the directory going.
    rm("_archive")
    rm("_ops")
    rm(".base")

    # 7. the config, rewritten to layout 2
    cfg["layout"] = LAYOUT
    cfg.pop("methodology", None)              # the seam dissolved: kb IS the methodology
    cfg.pop("principals", None)               # the grants table is the roster now
    cfg.setdefault("curation", "self")
    cfg.setdefault("curator", "")
    zones = {}
    for zone, d in (cfg.get("zones") or {}).items():
        kind = (d or {}).get("kind") if isinstance(d, dict) else None
        if kind in ("machinery", "archive"):
            continue                          # both directories are gone
        zones["_raw" if zone == "raw" else zone] = d
    cfg["zones"] = zones
    (root / ".kb" / "base.yml").write_text(
        yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    (root / ".gitignore").write_text(".kb/cache/\n", encoding="utf-8")
    for d in (root / ".kb" / "pending", root / ".kb" / "work",
              root / ".kb" / "cache", root / "_raw"):
        d.mkdir(parents=True, exist_ok=True)

    base_obj = Base(root)
    agent, author, _ = acting(ctx.obj, base_obj)
    git(root, "add", "-A")
    base_obj.commit("migrate", ["."],
                    f"{base_obj.cfg.get('name', root.name)}: layout 1 -> {LAYOUT}",
                    agent, author)

    print(f"migrated {root} to layout {LAYOUT}.")
    for m in moved:
        print(f"  moved   {m}")
    for d in dropped:
        print(f"  dropped {d} (history keeps it)")
    print()
    print("Two things to do by hand:")
    print("  1. `uv tool uninstall aos-base` — the old `base` command otherwise keeps "
          "shadowing on PATH.")
    print("  2. Re-read AGENTS.md: its grants rows still name layout 1 paths "
          "(raw/**, _ops/**, state.yaml), and a stale glob refuses SILENTLY.")
