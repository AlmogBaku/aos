"""`migrate rendered` — move a household's renders out of `personal/` into `rendered/`.

Before capability-lifecycle 0.7.0 a render lived in the user's source repo: a shipped
package's at `personal/capabilities/<id>/<subtree>/` (beside its MOD.md), the user's own
package's at `personal/renders/<id>/`. Now every render lives at `rendered/<id>/`. The move
runs in three steps, and the old paths keep resolving until the last one:

  (no flag)  the plan: writes nothing but its state file — the scan set and the old renders
             it holds the next two steps to
  --apply    copy each render (text files rewritten to the new paths), re-point every link,
             rewrite the lockfile and harness.yml — the old renders stay where they are
  --finish   refuse while anything still names an old render path or links into one;
             otherwise send the old renders to the OS trash

Between --apply and --finish the installer fixes each OUTSIDE REFERENCE through its owner:
a MOD.md answer through capability-evolve, a harness file (a hook command, a cron script)
through the cheat-sheet's steps, an own package's baked path in its source. Nothing here
edits those files: they belong to someone else, and some of them are security walls.

The scan reads harness homes, which hold keys, so every reference is printed as
`path:line` and never with the matched text."""

import fnmatch
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from ..constants import HARNESS_REL
from ..errors import Exit, fail
from ..household import find_home
from ..lockfile import link_target, load_lock, save_lock, sha256
from ..rendered import ensure_rendered_root, rendered_root, text_of, trash

app = typer.Typer(help="one-time household migrations")

STATE_REL = Path(".aos") / "migrate-rendered.yaml"
MIGRATING = ".migrating"
# Always skipped while scanning, on every harness: VCS internals, build caches, bytecode,
# databases, logs and transcripts, and the rendered tree's own in-flight directories. Each
# harness's own skip list (sessions, request dumps, backups…) lives in its cheat-sheet and
# arrives as --ignore.
BUILTIN_IGNORE = (".git", "node_modules", "__pycache__", ".venv", ".pytest_cache", "*.pyc",
                  "*.db", "*.db-*", "*.sqlite", "*.sqlite3", "*.log", "*.jsonl", "*.bak-*",
                  ".staging", ".replaced", MIGRATING)
PATH_CHARS = r"[A-Za-z0-9._-]"


# -- paths, compared the way the lockfile records them -------------------------------

def _rel(path: Path, root: Path) -> Optional[Path]:
    """`path` relative to `root`, or None. Compared both lexically and resolved: the
    lockfile records artifacts resolved but link targets lexically, so a household under
    a symlinked path has both spellings of one location in a single entry."""
    # Fixed order, lexical first — never a set: a set's order follows string hashing, which
    # varies per process, and a caller that keeps only the first match would then pick a
    # different spelling on every run.
    for p, r in ((path, root), (path, root.resolve()),
                 (path.resolve(), root), (path.resolve(), root.resolve())):
        if p == r or r in p.parents:
            return p.relative_to(r)
    return None


def _under(path: Path, roots) -> bool:
    return any(_rel(path, r) is not None for r in roots)


def _tails(home: Path, pairs: list[tuple[Path, Path]]) -> list[re.Pattern]:
    """Detection only, never rewrite: each old render's household-relative tail
    (`personal/renders/foo`, `personal/capabilities/bar/skills`), behind any prefix at all.
    It catches the spellings no list can enumerate — `"$AOS_HOME"/personal/…`,
    `${AOS_HOME:-$HOME/aos}/personal/…` — so --finish cannot trash a render a script still
    names. A false positive here only blocks."""
    out = []
    for old, _ in pairs:
        for base in (home, home.resolve()):
            rel = _rel(old, base)
            if rel is not None:
                out.append(re.compile(f"(?<!{PATH_CHARS})" + re.escape(os.fspath(rel))
                                      + f"(?!{PATH_CHARS})"))
                break
    return out


def _map(path: Path, pairs: list[tuple[Path, Path]]) -> Optional[Path]:
    for old, new in pairs:
        rel = _rel(path, old)
        if rel is not None:
            return new / rel
    return None


# -- what moves where ----------------------------------------------------------

def _own(home: Path, cap: str) -> bool:
    return (home / "personal" / "capabilities" / cap / "CAPABILITY.md").is_file()


def _old_roots(home: Path, lock: dict) -> dict[str, list[tuple[Path, Path]]]:
    """Per capability, the (old, new) directory pairs its render moves between — found by
    ownership, never by a list of exceptions. An own package's render is its whole
    `personal/renders/<id>/`. A shipped package's is each top-level subtree of
    `personal/capabilities/<id>/` that a recorded artifact or link target lies in — so its
    MOD.md, which no record names, never moves. An entry that records no artifacts (a
    plugin-only package) is found from its link targets."""
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
        subs = set()
        for p in recorded:
            rel = _rel(p, base)
            if rel is not None and len(rel.parts) > 1:
                subs.add(rel.parts[0])
        pairs = [(base / s, new / s) for s in sorted(subs) if (base / s).is_dir()]
        if pairs:
            roots[cap] = pairs
    return roots


def _prefixes(home: Path, pairs: list[tuple[Path, Path]]) -> list[tuple[re.Pattern, str]]:
    """One substitution per spelling of each old directory, each anchored on a path
    boundary (so `renders/foo` never rewrites `renders/foo-bar`):

      the absolute path, and its resolved form when the household sits under a symlink;
      `~/…`, `$HOME/…`, `${HOME}/…` when it sits under $HOME;
      `$AOS_HOME/…`, `${AOS_HOME}/…`, `<aos_home>/…` relative to the household.

    A hook command, a cron wrapper or a fallback baked into a script may use any of these.
    One the scan cannot spell passes --finish, which then trashes what it names — so a
    false positive here only blocks, and a missing spelling is the dangerous direction."""
    subs: list[tuple[re.Pattern, str]] = []
    home_dir = Path.home()
    for old, new in pairs:
        spellings = {(os.fspath(old), os.fspath(new))}
        if old.resolve() != old:
            spellings.add((os.fspath(old.resolve()), os.fspath(new.resolve())))
        # Every distinct $HOME-relative spelling — lexical and resolved — not just the first:
        # a household at `~/aos -> ~/real-aos` is written both ways.
        for o_abs, n_abs in ((old, new), (old.resolve(), new.resolve())):
            if home_dir in o_abs.parents:
                rel_o = o_abs.relative_to(home_dir)
                rel_n = n_abs.relative_to(home_dir) if home_dir in n_abs.parents else rel_o
                for pre in ("~/", "$HOME/", "${HOME}/"):
                    spellings.add((pre + os.fspath(rel_o), pre + os.fspath(rel_n)))
        rel_a, rel_an = _rel(old, home), _rel(new, home)
        if rel_a is not None and rel_an is not None:
            for pre in ("$AOS_HOME/", "${AOS_HOME}/", "<aos_home>/"):
                spellings.add((pre + os.fspath(rel_a), pre + os.fspath(rel_an)))
        for o, n in sorted(spellings, key=lambda s: -len(s[0])):
            subs.append((re.compile(re.escape(o) + f"(?!{PATH_CHARS})"), n))
    return subs


# -- scanning -------------------------------------------------------------------

def _ignored(rel: str, name: str, ignore) -> bool:
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


def _walk(top: Path, user_ignore, skip: list[Path]):
    """(path, ignored) for every file and symlink under `top`, never following links.
    The built-in skips are never entered. A directory the user's --ignore matches IS
    walked, with everything beneath it marked ignored: its text is not searched, but its
    links are still counted, so the plan can say how many old-render links it leaves
    alone. `skip` holds the old renders themselves: they are copied, not referenced."""
    if top.is_symlink() or not top.is_dir():
        if top.exists() or top.is_symlink():
            yield top, False
        return
    stack = [(top, False)]
    while stack:
        d, ign = stack.pop()
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError:
            continue
        for e in entries:
            p = Path(e.path)
            rel = os.fspath(p.relative_to(top))
            if _ignored(rel, e.name, BUILTIN_IGNORE):
                continue
            mark = ign or _ignored(rel, e.name, user_ignore)
            if e.is_symlink():
                yield p, mark
            elif e.is_dir(follow_symlinks=False):
                if not any(p == s or s in p.parents for s in skip):
                    stack.append((p, mark))
            elif e.is_file(follow_symlinks=False):
                yield p, mark


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
    rel = _rel(path, personal)
    if rel is not None:
        if path.name == "MOD.md":
            return "MOD answer → capability-evolve"
        if len(rel.parts) > 2 and rel.parts[0] == "capabilities" and rel.parts[1] in own_caps:
            return f"source of your package '{rel.parts[1]}' → edit it, then re-render"
        return "personal/ file → edit it"
    if _rel(path, rendered_root(home)) is not None:
        return "a live render → re-render it through staging and the gate"
    if path.suffix in (".yaml", ".yml", ".json", ".toml"):
        return "harness config → change it through the cheat-sheet's steps"
    return "harness-side file (script, prompt, skill) → edit it"


def _scan(home: Path, lock: dict, roots: dict, scan: list[Path], ignore: list[str]):
    """Across the scan set: outside references (path, line, owner); links into an old
    render to re-point {link: target}; links into an old render that dangle, or sit inside
    an --ignore'd directory (both left alone, and reported); and links into the rest of
    `personal/` (left alone, and reported)."""
    all_pairs = [pr for pairs in roots.values() for pr in pairs]
    olds = [old for old, _ in all_pairs]
    subs = _prefixes(home, all_pairs)
    # One alternation, tried once per file before any line is: a household has dozens of
    # render roots times several spellings, and testing each line against every pattern
    # separately made a scan of a real harness home take many minutes.
    pats = [rx.pattern for rx, _ in subs] + [rx.pattern for rx in _tails(home, all_pairs)]
    detect = re.compile("|".join(f"(?:{p})" for p in pats)) if pats else None
    own_caps = {c for c in lock["installs"] if _own(home, c)}
    personal = home / "personal"
    refs, links, seen = [], {}, set()
    dangling, in_ignored, into_personal = [], [], []
    for top in scan:
        for p, ign in _walk(top, ignore, olds):
            if p in seen:
                continue
            seen.add(p)
            if p.is_symlink():
                t = Path(os.path.normpath(os.path.join(os.fspath(p.parent), os.readlink(p))))
                if _under(t, olds):
                    if ign:
                        in_ignored.append((p, t))
                    elif not t.exists():
                        dangling.append((p, t))
                    else:
                        links[p] = t
                elif _rel(t, personal) is not None:
                    into_personal.append((p, t))
                continue
            if ign:
                continue
            text = text_of(p)
            if text is None or detect is None or not detect.search(text):
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if detect.search(line):
                    refs.append((p, n, _owner(p, home, own_caps)))
    recorded = set()
    for entry in lock["installs"].values():
        for link, target in {**(entry.get("links") or {}), **(entry.get("uses_links") or {})}.items():
            recorded.add(Path(link))
            t = Path(target)
            if _under(t, olds) and Path(link) not in dict(dangling):
                links.setdefault(Path(link), t)
    # A recorded link is the lockfile's to judge (re-pointed, or drift in _dirty): never also
    # counted as an unrecorded dangling one or as one left alone in an ignored directory.
    dangling = [(l, t) for l, t in dangling if l not in recorded]
    in_ignored = [(l, t) for l, t in in_ignored if l not in recorded]
    return refs, links, dangling, in_ignored, into_personal


# -- integrity --------------------------------------------------------------------

def _git_status(personal: Path, rels: list[str], ignored: bool) -> tuple[Optional[list[str]], str]:
    """`git status --porcelain` lines for `rels`, or (None, why) when git cannot answer.
    An unanswerable status is NOT a clean one: for an entry with no recorded artifacts it
    is the only evidence there is."""
    if not (personal / ".git").exists():
        return None, f"{personal} is not a git repository"
    cmd = ["git", "-C", os.fspath(personal), "status", "--porcelain", "--untracked-files=all"]
    if ignored:
        cmd.append("--ignored")
    try:
        r = subprocess.run(cmd + ["--", *rels], capture_output=True, text=True)
    except OSError as err:
        return None, f"git could not run ({err})"
    if r.returncode != 0:
        first = ((r.stderr or "").strip().splitlines() or ["no message"])[0]
        return None, f"git status failed: {first}"
    return r.stdout.splitlines(), ""


def _dirty(home: Path, lock: dict, roots: dict, dangling) -> list[str]:
    """What the copy must not bless, and what --apply must not overwrite:

      an artifact whose hash no longer matches its record (a hand-edit nobody captured);
      anything `git status --porcelain` reports in an old render, untracked files included
        — and a git that cannot answer, which is not a clean answer;
      a recorded link into an old render that is no longer what the lockfile says (gone,
        replaced by a file, re-pointed by hand, dangling) — --apply would otherwise put it
        back or overwrite it, and the plan would show that as an ordinary re-point;
      an unrecorded link into an old render that already dangles."""
    out = []
    all_pairs = [pr for pairs in roots.values() for pr in pairs]
    olds = [old for old, _ in all_pairs]
    for cap, entry in sorted(lock["installs"].items()):
        for path, sha in (entry.get("artifacts") or {}).items():
            p = Path(path)
            if _under(p, olds):
                if not p.is_file():
                    out.append(f"{cap}: MISSING {path}")
                elif sha256(p) != sha:
                    out.append(f"{cap}: DRIFT {path}")
        for path, target in {**(entry.get("links") or {}), **(entry.get("uses_links") or {})}.items():
            if not _under(Path(target), olds):
                continue
            p = Path(path)
            if not p.is_symlink():
                out.append(f"{cap}: {'NOT A LINK' if p.exists() else 'MISSING LINK'} {path}")
            elif link_target(p) not in (target, os.fspath(_map(Path(target), all_pairs))):
                # Pointing at its NEW target is this migration's own work (a re-run after a
                # crash mid-re-point); anything else is a hand change.
                out.append(f"{cap}: RELINKED {path} -> {link_target(p)} (recorded: {target})")
            elif not p.exists():
                out.append(f"{cap}: DANGLING LINK {path} -> {target}")
    for link, target in dangling:
        out.append(f"unrecorded: DANGLING LINK {link} -> {target}")
    personal = home / "personal"
    rels = [os.fspath(r) for o in olds if (r := _rel(o, personal)) is not None]
    if rels:
        lines, why = _git_status(personal, rels, ignored=False)
        if lines is None:
            out.append(f"cannot check for uncommitted renders: {why}")
        else:
            out += [f"uncommitted: {line}" for line in lines if line.strip()]
    return out


def _carried_ignored(home: Path, roots: dict) -> list[str]:
    """Gitignored files the copy would carry (bytecode is left behind, so it is not listed)."""
    personal = home / "personal"
    olds = [old for pairs in roots.values() for old, _ in pairs]
    rels = [os.fspath(r) for o in olds if (r := _rel(o, personal)) is not None]
    if not rels:
        return []
    lines, _ = _git_status(personal, rels, ignored=True)
    return [line[3:] for line in (lines or []) if line.startswith("!! ")
            and "__pycache__" not in line and not line.endswith(".pyc")]


# -- the state file ---------------------------------------------------------------

def _state(home: Path) -> Optional[dict]:
    p = home / STATE_REL
    return yaml.safe_load(p.read_text()) if p.is_file() else None


def _write_state(home: Path, st: dict) -> None:
    p = home / STATE_REL
    tmp = p.with_suffix(".yaml.tmp")
    tmp.write_text(yaml.safe_dump(st, sort_keys=False))
    os.replace(tmp, p)


def _roots_of(st: dict) -> dict[str, list[tuple[Path, Path]]]:
    return {c: [(Path(o), Path(n)) for o, n in prs] for c, prs in (st.get("roots") or {}).items()}


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


def _prune_empty(top: Path) -> None:
    """Remove empty directories under (and including) `top` — never a file."""
    if not top.is_dir():
        return
    for d in sorted((p for p in top.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    if not any(top.iterdir()):
        top.rmdir()


def _nothing() -> None:
    print("nothing to migrate: every render already lives under rendered/")
    raise typer.Exit(0)


# -- the three steps ----------------------------------------------------------------

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
    asked = {os.fspath(Path(s).expanduser().absolute()) for s in (scan or [])}

    # The old renders are derived from the lockfile ONCE, by the plan step, and saved with
    # the scan set. Every later step reads them from the state: after --apply the lockfile
    # names only new paths, and a step that re-derived them after a crash mid-apply would
    # silently lose every shipped package from the migration.
    if step == "plan" and not applied:
        roots = _old_roots(home, lock)
        # A re-plan never narrows what an earlier plan found: after a crash between the
        # lockfile write and the state write, the lockfile no longer names the shipped
        # packages' old subtrees, but they are still on disk and still to be trashed.
        for cap, prs in _roots_of(st or {}).items():
            have = {o for o, _ in roots.get(cap, [])}
            roots.setdefault(cap, []).extend((o, n) for o, n in prs if o not in have and o.exists())
        roots = {c: prs for c, prs in roots.items() if prs}
        if not roots:
            _nothing()
        dirs = [Path(d) for d in sorted({os.fspath(home / "personal"),
                                         *[os.fspath(h) for h in _harness_homes(lock)], *asked})]
        ign = list(ignore or [])
    else:
        if st is None:
            if not _old_roots(home, lock):
                _nothing()
            fail(Exit.MIGRATE_BLOCKED, "no approved plan — run `aos-cap migrate rendered` "
                                       "(the plan step) first")
        wider = sorted(set(ignore or []) - set(st.get("ignore", [])))
        if wider:
            fail(Exit.MIGRATE_BLOCKED, f"--ignore {wider} would scan less than the approved plan")
        roots = _roots_of(st)
        dirs = [Path(d) for d in sorted(set(st["scan"]) | asked)]
        ign = list(st.get("ignore", []))
    if step == "finish":
        # Copies were rewritten, so anything in a live render still naming an old path —
        # an absolute symlink copied verbatim, a spelling the rewrite missed — is found here.
        dirs = sorted(set(dirs) | {rendered_root(home)})
    all_pairs = [pr for prs in roots.values() for pr in prs]
    subs = _prefixes(home, all_pairs)
    refs, links, dangling, in_ignored, into_personal = _scan(home, lock, roots, dirs, ign)

    if step == "plan" and applied:
        print(f"applied; before --finish: {len(refs)} outside reference(s), "
              f"{len(links)} link(s) into an old render")
        for p, n, owner in refs:
            print(f"  {p}:{n}  [{owner}]")
        for link, target in sorted(links.items()):
            print(f"  LINK {link} -> {target}")
        return

    if step == "plan":
        print("# migrate rendered — the plan (nothing written but its state file)\n")
        print("## moves")
        for cap, prs in roots.items():
            for old, new in prs:
                print(f"  {cap}: {old} -> {new}")
        print(f"\n## links re-pointed ({len(links)})")
        for link, target in sorted(links.items()):
            print(f"  {link}: {target} -> {_map(target, all_pairs)}")
        print(f"\n## links into old renders the move cannot re-point: {len(dangling)} dangling "
              f"(listed under drift), {len(in_ignored)} inside --ignore'd directories "
              f"(--finish refuses while any remain)")
        for link, target in sorted(in_ignored):
            print(f"  {link} -> {target}")
        print(f"\n## links into personal/ outside any render, left alone ({len(into_personal)})")
        for link, target in sorted(into_personal):
            print(f"  {link} -> {target}")
        print("\n## lockfile and harness.yml paths rewritten")
        for cap, entry in sorted(lock["installs"].items()):
            for p in sorted(entry.get("artifacts") or {}):
                if _map(Path(p), all_pairs):
                    print(f"  {cap} artifact: {p} -> {_map(Path(p), all_pairs)}")
            for key in ("links", "uses_links"):
                for l, t in sorted((entry.get(key) or {}).items()):
                    if _map(Path(t), all_pairs):
                        print(f"  {cap} {key[:-1]}: {l}: {t} -> {_map(Path(t), all_pairs)}")
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
        dirty = _dirty(home, lock, roots, dangling)
        print(f"\n## drift — renders, links, uncommitted changes ({len(dirty)}) — "
              f"--apply refuses while any remain")
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
        print("  skipped everywhere: " + ", ".join(BUILTIN_IGNORE))
        print("  --ignore: " + (", ".join(ign) if ign else "(none)"))
        _write_state(home, {"scan": [os.fspath(d) for d in dirs], "ignore": ign,
                            "roots": {c: [[os.fspath(o), os.fspath(n)] for o, n in prs]
                                      for c, prs in roots.items()}})
        return

    if step == "apply":
        dirty = _dirty(home, lock, roots, dangling)
        if dirty:
            for line in dirty:
                print(line)
            fail(Exit.MIGRATE_BLOCKED, f"{len(dirty)} problem(s) — fold drift into MOD.md; for a "
                                       f"changed link ask the user, then re-link it by the "
                                       f"lockfile or re-record the entry without it; commit or "
                                       f"remove uncommitted files; then plan again")
        ensure_rendered_root(home)
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
                    f.write_bytes(new_text.encode("utf-8"))
            new.parent.mkdir(parents=True, exist_ok=True)
            os.rename(tmp, new)
        _prune_empty(work)
        # 2. re-point every link: a dot-named temporary link the harness ignores, then one
        #    atomic replace; leftovers of a crashed run are swept first. A destination that
        #    does not exist stops the step BEFORE the link is touched.
        for link, target in sorted(links.items()):
            dest = _map(target, all_pairs)
            if dest is None or not (dest.exists() or dest.is_symlink()):
                fail(Exit.MIGRATE_BLOCKED, f"{link} -> {target}: its new target {dest} does "
                                           f"not exist; nothing was changed for this link")
            tmp = link.parent / f".{link.name}.aos-migrate"
            if tmp.is_symlink():
                tmp.unlink()
            os.symlink(os.fspath(dest), tmp)
            os.replace(tmp, link)
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
                for f in (p for p in new.rglob("*") if p.is_file() and not p.is_symlink()
                          and "__pycache__" not in p.parts and p.suffix != ".pyc"):
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
        st["applied"] = True
        _write_state(home, st)
        print(f"applied: {len(all_pairs)} render subtree(s) copied, {len(links)} link(s) "
              f"re-pointed, lockfile rewritten; the old renders stay until --finish")
        print(f"{len(refs)} outside reference(s) still name an old path — fix each through its owner:")
        for p, n, owner in refs:
            print(f"  {p}:{n}  [{owner}]")
        return

    # finish
    if refs or links or dangling or in_ignored:
        for p, n, owner in refs:
            print(f"  {p}:{n}  [{owner}]")
        for link, target in sorted(links.items()) + sorted(dangling) + sorted(in_ignored):
            print(f"  LINK {link} -> {target}")
        fail(Exit.MIGRATE_BLOCKED, f"{len(refs)} outside reference(s) and "
                                   f"{len(links) + len(dangling) + len(in_ignored)} link(s) still "
                                   f"name an old render — nothing was trashed")
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
