"""`migrate rendered` — move a household's renders out of `personal/` into `rendered/`.

Before capability-lifecycle 0.7.0 a render lived in the user's source repo: a shipped
package's at `personal/capabilities/<id>/<subtree>/` (beside its MOD.md), the user's own
package's at `personal/renders/<id>/`. Now every render lives at `rendered/<id>/`. The move
runs in three steps, and the old paths keep resolving until the last one:

  (no flag)  the plan: writes nothing but the scan set it will hold the next steps to
  --apply    copy each render (text files rewritten to the new paths), re-point every link,
             rewrite the lockfile and harness.yml — the old renders stay where they are
  --finish   refuse while anything still names an old render path or links into one;
             otherwise send the old renders to the OS trash

Between --apply and --finish the installer fixes each OUTSIDE REFERENCE through its owner:
a MOD.md answer through capability-evolve, a harness config line (a hook command, a cron
script) through the harness's own CLI, an own package's baked path in its source. Nothing
here edits those files: they belong to someone else, and some of them are security walls.

The scan reads harness homes, which hold keys, so every reference is printed as
`path:line` and never with the matched text."""

import fnmatch
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from ..constants import HARNESS_REL, LOCK_REL
from ..errors import Exit, fail
from ..household import find_home
from ..lockfile import load_lock, save_lock, sha256
from ..rendered import rendered_root, staging_root, text_of, trash

app = typer.Typer(help="one-time household migrations")

STATE_REL = Path(".aos") / "migrate-rendered.yaml"
MIGRATING = ".migrating"
# Always skipped while scanning, on every harness: VCS internals, build caches, bytecode,
# databases, logs and transcripts. Each harness's own skip list (sessions, request dumps,
# backups…) lives in its cheat-sheet and arrives as --ignore.
BUILTIN_IGNORE = (".git", "node_modules", "__pycache__", ".venv", ".pytest_cache", "*.pyc",
                  "*.db", "*.db-*", "*.sqlite", "*.sqlite3", "*.log", "*.jsonl", "*.bak-*")
PATH_CHARS = r"[A-Za-z0-9._-]"


# -- what moves where ----------------------------------------------------------

def _own(home: Path, cap: str) -> bool:
    return (home / "personal" / "capabilities" / cap / "CAPABILITY.md").is_file()


def _old_roots(home: Path, lock: dict) -> dict[str, list[tuple[Path, Path]]]:
    """Per capability, the (old, new) directory pairs its render moves between — found by
    ownership, never by a list of exceptions. An own package's render is its whole
    `personal/renders/<id>/`. A shipped package's is each top-level subtree of
    `personal/capabilities/<id>/` that a recorded artifact or link target lies in — so its
    MOD.md, which no record names, never moves. An entry that records no artifacts
    (a plugin-only package) is found from its link targets."""
    personal = home / "personal"
    recorded: list[Path] = []
    for entry in lock["installs"].values():
        recorded += [Path(p) for p in (entry.get("artifacts") or {})]
        recorded += [Path(t) for t in (entry.get("links") or {}).values()]
        recorded += [Path(t) for t in (entry.get("uses_links") or {}).values()]
    roots: dict[str, list[tuple[Path, Path]]] = {}
    for cap in sorted(lock["installs"]):
        new = rendered_root(home) / cap
        if _own(home, cap):
            old = personal / "renders" / cap
            if old.is_dir():
                roots[cap] = [(old, new)]
            continue
        base = personal / "capabilities" / cap
        subs = sorted({p.relative_to(base).parts[0] for p in recorded
                       if base in p.parents and len(p.relative_to(base).parts) > 1})
        pairs = [(base / s, new / s) for s in subs if (base / s).is_dir()]
        if pairs:
            roots[cap] = pairs
    return roots


def _prefixes(home: Path, pairs: list[tuple[Path, Path]]) -> list[tuple[re.Pattern, str]]:
    """One substitution per pair, for the absolute spelling and, when the household sits
    under $HOME, the `~/…` one. Anchored on a path boundary, so `renders/triage` never
    rewrites `renders/triage-dashboard`."""
    subs = []
    home_dir = Path.home()
    for old, new in pairs:
        spellings = [(os.fspath(old), os.fspath(new))]
        if home_dir in old.parents:
            spellings.append(("~/" + os.fspath(old.relative_to(home_dir)),
                              "~/" + os.fspath(new.relative_to(home_dir))))
        for o, n in spellings:
            subs.append((re.compile(re.escape(o) + f"(?!{PATH_CHARS})"), n))
    return subs


def _map(path: Path, pairs: list[tuple[Path, Path]]) -> Optional[Path]:
    for old, new in pairs:
        if path == old or old in path.parents:
            return new / path.relative_to(old)
    return None


# -- scanning -------------------------------------------------------------------

def _ignored(rel: str, name: str, ignore: list[str]) -> bool:
    """A glob without `/` matches a basename anywhere; one with `/` (`cron/output`) matches
    that path at any depth, so a per-profile `profiles/x/cron/output` is skipped too."""
    for g in ignore:
        g = g.rstrip("/")
        if "/" in g:
            if fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(rel, "*/" + g):
                return True
        elif fnmatch.fnmatch(name, g):
            return True
    return False


def _walk(top: Path, ignore: list[str], skip: list[Path]):
    """Every file and symlink under `top`, never following links, never entering an
    ignored directory or one of `skip` (the old renders themselves: they are copied, not
    referenced)."""
    if top.is_symlink() or not top.is_dir():
        if top.exists() or top.is_symlink():
            yield top
        return
    for dirpath, dirnames, filenames in os.walk(top, followlinks=False):
        d = Path(dirpath)
        keep = []
        for name in dirnames:
            p = d / name
            if p.is_symlink():
                filenames.append(name)
            elif not (_ignored(os.fspath(p.relative_to(top)), name, ignore)
                      or any(p == s or s in p.parents for s in skip)):
                keep.append(name)
        dirnames[:] = keep
        for name in filenames:
            p = d / name
            if not _ignored(os.fspath(p.relative_to(top)), name, ignore):
                yield p


def _harness_homes(lock: dict) -> list[Path]:
    """The home each recorded link lives under: the top-level dot-directory beneath $HOME
    (`~/.hermes`, `~/.claude`), else the link's own directory."""
    homes = set()
    h = Path.home()
    for entry in lock["installs"].values():
        for link in list((entry.get("links") or {})) + list((entry.get("uses_links") or {})):
            p = Path(link)
            if h in p.parents and p.relative_to(h).parts[0].startswith("."):
                homes.add(h / p.relative_to(h).parts[0])
            else:
                homes.add(p.parent)
    return sorted(homes)


def _owner(path: Path, home: Path, own_caps: set[str]) -> str:
    personal = home / "personal"
    if personal in path.parents:
        if path.name == "MOD.md":
            return "MOD answer → capability-evolve"
        rel = path.relative_to(personal).parts
        if len(rel) > 2 and rel[0] == "capabilities" and rel[1] in own_caps:
            return f"source of your package '{rel[1]}' → edit it, then re-render"
        return "personal/ file → edit it"
    return "harness file → change it with the harness's own CLI"


def _scan(home: Path, lock: dict, roots: dict, scan: list[Path], ignore: list[str]):
    """(outside references, links into an old render) across the scan set."""
    all_pairs = [pr for pairs in roots.values() for pr in pairs]
    olds = [old for old, _ in all_pairs]
    subs = _prefixes(home, all_pairs)
    own_caps = {c for c in lock["installs"] if _own(home, c)}
    refs, links, seen = [], {}, set()
    for top in scan:
        for p in _walk(top, ignore, olds):
            if p in seen:
                continue
            seen.add(p)
            if any(p == o or o in p.parents for o in olds):
                continue
            if p.is_symlink():
                t = Path(os.path.normpath(os.path.join(os.fspath(p.parent), os.readlink(p))))
                if any(t == o or o in t.parents for o in olds):
                    links[p] = t
                continue
            text = text_of(p) if p.is_file() else None
            if text is None:
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if any(rx.search(line) for rx, _ in subs):
                    refs.append((p, n, _owner(p, home, own_caps)))
    for entry in lock["installs"].values():
        for link, target in {**(entry.get("links") or {}), **(entry.get("uses_links") or {})}.items():
            t = Path(target)
            if any(t == o or o in t.parents for o in olds):
                links.setdefault(Path(link), t)
    return refs, links


# -- integrity --------------------------------------------------------------------

def _dirty(home: Path, lock: dict, roots: dict) -> list[str]:
    """Renders the copy must not bless: an artifact whose hash no longer matches its record
    (a hand-edit nobody captured), and anything `git status --porcelain` reports in an old
    render — untracked files included, since for an entry with no recorded artifacts a
    clean git status is the only evidence there is. Once copied, the new lockfile hashes
    whatever was there."""
    out = []
    olds = [old for pairs in roots.values() for old, _ in pairs]
    for cap, entry in sorted(lock["installs"].items()):
        for path, sha in (entry.get("artifacts") or {}).items():
            p = Path(path)
            if any(p == o or o in p.parents for o in olds):
                if not p.is_file():
                    out.append(f"{cap}: MISSING {path}")
                elif sha256(p) != sha:
                    out.append(f"{cap}: DRIFT {path}")
    personal = home / "personal"
    if (personal / ".git").exists() and olds:
        rels = [os.fspath(o.relative_to(personal)) for o in olds]
        r = subprocess.run(["git", "-C", os.fspath(personal), "status", "--porcelain",
                            "--untracked-files=all", "--", *rels],
                           capture_output=True, text=True)
        out += [f"uncommitted: {line}" for line in r.stdout.splitlines() if line.strip()]
    return out


def _carried_ignored(home: Path, roots: dict) -> list[str]:
    """Gitignored files the copy would carry (bytecode is left behind, so it is not listed)."""
    personal = home / "personal"
    olds = [old for pairs in roots.values() for old, _ in pairs]
    if not (personal / ".git").exists() or not olds:
        return []
    rels = [os.fspath(o.relative_to(personal)) for o in olds]
    r = subprocess.run(["git", "-C", os.fspath(personal), "status", "--porcelain", "--ignored",
                        "--untracked-files=all", "--", *rels], capture_output=True, text=True)
    return [line[3:] for line in r.stdout.splitlines() if line.startswith("!! ")
            and "__pycache__" not in line and not line.endswith(".pyc")]


# -- the three steps ----------------------------------------------------------------

def _state(home: Path) -> Optional[dict]:
    p = home / STATE_REL
    return yaml.safe_load(p.read_text()) if p.is_file() else None


def _resolve_scan(home: Path, lock: dict, scan: list[str], ignore: list[str], step: str):
    """The plan step chooses the scan set and saves it. Every later step scans the saved
    set (plus any --scan it is given, which can only widen it) and refuses a new --ignore,
    so the step that trashes the old renders has looked everywhere the approved plan did."""
    asked = {os.fspath(Path(s).expanduser().absolute()) for s in scan}
    if step == "plan":
        dirs = sorted({os.fspath(home / "personal"),
                       *[os.fspath(h) for h in _harness_homes(lock)], *asked})
        return [Path(d) for d in dirs], list(BUILTIN_IGNORE) + list(ignore)
    st = _state(home)
    if st is None:
        fail(Exit.MIGRATE_BLOCKED, "no approved plan — run `aos-cap migrate rendered` "
                                   "(the plan step) first")
    wider = sorted(set(ignore) - set(st.get("ignore", [])))
    if wider:
        fail(Exit.MIGRATE_BLOCKED, f"--ignore {wider} would scan less than the approved plan")
    return [Path(d) for d in sorted(set(st["scan"]) | asked)], list(st["ignore"])


def _rewrite_diff(path: Path, subs) -> list[str]:
    text = text_of(path)
    if text is None:
        return []
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        new = line
        for rx, rep in subs:
            new = rx.sub(rep, new)
        if new != line:
            out += [f"  {path}:{n}", f"    - {line.strip()}", f"    + {new.strip()}"]
    return out


def _nothing() -> None:
    print("nothing to migrate: every render already lives under rendered/")
    raise typer.Exit(0)


@app.command("rendered", help="move renders from personal/ to rendered/ (plan; --apply; --finish)")
def cmd_rendered(
    ctx: typer.Context,
    apply: Annotated[bool, typer.Option("--apply", help="copy, re-point links, rewrite the lockfile")] = False,
    finish: Annotated[bool, typer.Option("--finish", help="refuse while anything names an old path; then trash the old renders")] = False,
    scan: Annotated[Optional[list[str]], typer.Option("--scan", help="repeatable: another directory to scan (plan step)")] = None,
    ignore: Annotated[Optional[list[str]], typer.Option("--ignore", help="repeatable glob to skip while scanning (plan step)")] = None,
) -> None:
    if apply and finish:
        fail(Exit.GENERIC, "--apply and --finish are separate steps")
    home = find_home(ctx.obj)
    lock = load_lock(home)
    step = "apply" if apply else "finish" if finish else "plan"
    st = _state(home)
    applied = bool(st and st.get("applied"))
    # Once --apply has run, the lockfile names only new paths, so the old renders are
    # known from the saved state, not re-derived.
    roots = ({c: [(Path(o), Path(n)) for o, n in prs] for c, prs in st["roots"].items()}
             if applied else _old_roots(home, lock))
    if not roots:
        _nothing()
    dirs, ign = _resolve_scan(home, lock, scan or [], ignore or [],
                              "reuse" if applied and step == "plan" else step)
    all_pairs = [pr for prs in roots.values() for pr in prs]
    subs = _prefixes(home, all_pairs)
    refs, links = _scan(home, lock, roots, dirs, ign)

    if step == "plan" and applied:
        print(f"applied; before --finish: {len(refs)} outside reference(s), "
              f"{len(links)} link(s) into an old render")
        for p, n, owner in refs:
            print(f"  {p}:{n}  [{owner}]")
        for link, target in sorted(links.items()):
            print(f"  LINK {link} -> {target}")
        return

    if step == "plan":
        print("# migrate rendered — the plan (nothing written but the scan set)\n")
        print("## moves")
        for cap, prs in roots.items():
            for old, new in prs:
                print(f"  {cap}: {old} -> {new}")
        print(f"\n## links re-pointed ({len(links)})")
        for link, target in sorted(links.items()):
            print(f"  {link}: {target} -> {_map(target, all_pairs)}")
        print("\n## lockfile and harness.yml paths rewritten")
        for cap, entry in sorted(lock["installs"].items()):
            n = sum(1 for p in (entry.get("artifacts") or {}) if _map(Path(p), all_pairs))
            m = sum(1 for t in {**(entry.get("links") or {}), **(entry.get("uses_links") or {})}.values()
                    if _map(Path(t), all_pairs))
            if n or m:
                print(f"  {cap}: {n} artifact paths, {m} link targets")
        hy = home / HARNESS_REL
        if hy.is_file():
            sheet = (yaml.safe_load(hy.read_text()) or {}).get("sheet")
            if sheet and _map(Path(sheet), all_pairs):
                print(f"  harness.yml sheet: {sheet} -> {_map(Path(sheet), all_pairs)}")
        print("\n## text the copy rewrites")
        for old, _ in all_pairs:
            for f in sorted(p for p in old.rglob("*") if p.is_file() and not p.is_symlink()
                            and "__pycache__" not in p.parts):
                for line in _rewrite_diff(f, subs):
                    print(line)
        dirty = _dirty(home, lock, roots)
        print(f"\n## renders with drift or uncommitted changes ({len(dirty)}) — --apply refuses while any remain")
        for line in dirty:
            print(f"  {line}")
        carried = _carried_ignored(home, roots)
        if carried:
            print(f"\n## gitignored files the copy carries ({len(carried)})")
            for line in carried:
                print(f"  {line}")
        print(f"\n## outside references ({len(refs)}) — fix each through its owner before --finish")
        for p, n, owner in refs:
            print(f"  {p}:{n}  [{owner}]")
        print("\n## scan set (saved; --apply and --finish reuse it)")
        for d in dirs:
            print(f"  {d}")
        (home / STATE_REL).write_text(yaml.safe_dump({"scan": [os.fspath(d) for d in dirs],
                                                      "ignore": ign}, sort_keys=False))
        return

    if step == "apply":
        dirty = _dirty(home, lock, roots)
        if dirty:
            for line in dirty:
                print(line)
            fail(Exit.MIGRATE_BLOCKED, f"{len(dirty)} render(s) have drift or uncommitted "
                                       f"changes — fold each into MOD.md or restore it first")
        work = rendered_root(home) / MIGRATING
        # 1. copy, each subtree via a scratch dir and one rename, so a crash mid-copy leaves
        #    nothing half-written under rendered/<id>; a re-run redoes only what is missing.
        for old, new in all_pairs:
            if new.exists():
                continue
            tmp = work / new.relative_to(rendered_root(home))
            if tmp.exists():
                trash(tmp)
            shutil.copytree(old, tmp, symlinks=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            for f in (p for p in tmp.rglob("*") if p.is_file() and not p.is_symlink()):
                text = text_of(f)
                if text is None:
                    continue
                new_text = text
                for rx, rep in subs:
                    new_text = rx.sub(rep, new_text)
                if new_text != text:
                    f.write_text(new_text)
            new.parent.mkdir(parents=True, exist_ok=True)
            os.rename(tmp, new)
        if work.is_dir() and not any(work.rglob("*")):
            shutil.rmtree(work)  # empty scratch directories only
        # 2. re-point every link: a dot-named temporary link the harness ignores, then one
        #    atomic replace; leftovers of a crashed run are swept first.
        for link, target in sorted(links.items()):
            dest = _map(target, all_pairs)
            tmp = link.parent / f".{link.name}.aos-migrate"
            if tmp.is_symlink():
                tmp.unlink()
            os.symlink(os.fspath(dest), tmp)
            os.replace(tmp, link)
            if not link.exists():
                fail(Exit.MIGRATE_BLOCKED, f"{link} -> {dest} does not resolve after the re-point")
        # 3. the lockfile and harness.yml, last.
        for cap, entry in lock["installs"].items():
            arts = {}
            for path, sha in (entry.get("artifacts") or {}).items():
                dest = _map(Path(path), all_pairs)
                if dest is None:
                    arts[path] = sha
                elif not dest.is_file():
                    continue  # bytecode the copy left behind: it is regenerated, not recorded
                else:
                    # The drift refusal above proved the old file matched its record,
                    # so the copy (rewritten or not) is the new baseline.
                    arts[os.fspath(dest)] = sha256(dest)
            for old, new in roots.get(cap, []):
                for f in (p for p in new.rglob("*") if p.is_file() and not p.is_symlink()):
                    arts.setdefault(os.fspath(f), sha256(f))
            entry["artifacts"] = arts
            for key in ("links", "uses_links"):
                entry[key] = {l: os.fspath(_map(Path(t), all_pairs) or t)
                              for l, t in (entry.get(key) or {}).items()}
        save_lock(home, lock)
        hy = home / HARNESS_REL
        if hy.is_file():
            rec = yaml.safe_load(hy.read_text()) or {}
            if rec.get("sheet") and _map(Path(rec["sheet"]), all_pairs):
                rec["sheet"] = os.fspath(_map(Path(rec["sheet"]), all_pairs))
                hy.write_text(yaml.safe_dump(rec, sort_keys=False))
        st = _state(home) or {}
        st.update({"applied": True,
                   "roots": {c: [[os.fspath(o), os.fspath(n)] for o, n in prs]
                             for c, prs in roots.items()}})
        (home / STATE_REL).write_text(yaml.safe_dump(st, sort_keys=False))
        print(f"applied: {len(all_pairs)} render subtree(s) copied, {len(links)} link(s) "
              f"re-pointed, lockfile rewritten; the old renders stay until --finish")
        print(f"{len(refs)} outside reference(s) still name an old path — fix each through its owner:")
        for p, n, owner in refs:
            print(f"  {p}:{n}  [{owner}]")
        return

    # finish
    if refs or links:
        for p, n, owner in refs:
            print(f"  {p}:{n}  [{owner}]")
        for link, target in sorted(links.items()):
            print(f"  LINK {link} -> {target}")
        fail(Exit.MIGRATE_BLOCKED, f"{len(refs)} outside reference(s) and {len(links)} link(s) "
                                   f"still name an old render — nothing was trashed")
    if not applied:
        fail(Exit.MIGRATE_BLOCKED, "run `aos-cap migrate rendered --apply` first")
    for old, new in all_pairs:
        if not new.exists():
            fail(Exit.MIGRATE_BLOCKED, f"{new} is missing — re-run --apply before --finish")
    for old, _ in all_pairs:
        if old.exists():
            trash(old)
    renders = home / "personal" / "renders"
    if renders.is_dir() and not any(renders.iterdir()):
        renders.rmdir()
    (home / STATE_REL).unlink()
    print(f"finished: {len(all_pairs)} old render subtree(s) are in the trash. Commit "
          f"personal/ — the renders' removal from it is that commit.")
