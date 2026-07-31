#!/usr/bin/env python3
"""Golden-render structural checks (RFC-002 tier 2, deterministic layer).

Modes:
  default      — validate committed snapshots under tests/golden/hermes/<name>/
  --live NAME  — validate the real materialized tree per PROTOCOL.md roots
Exits non-zero on any failure. No LLM anywhere in here.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

from ..constants import ORIGIN_FRONTMATTER_KEY
from ..repo import REPO_ROOT
from .normalize import SKIP, has_stamp, normalize_tree, origin_stamp
EXPECTATIONS = REPO_ROOT / "tests" / "golden" / "expectations"
GOLDEN_DIR = REPO_ROOT / "tests" / "golden" / "hermes"


def live_roots(exp):
    home = Path.home()
    roots = {
        "front": home / ".hermes" / "profiles" / "aos-test",
        "home": REPO_ROOT / "tests" / ".sandbox" / "aos-home",
        # The harness ROOT, for the shared dirs a profile does not own: `--script` files land in
        # ~/.hermes/scripts/ per the cheat-sheet's Materialization guide, which is the only place
        # Hermes reads them from. Snapshot mode has no equivalent — the root is outside every
        # profile tree — so a `root:` reference is live-only by construction.
        "root": home / ".hermes",
    }
    for a in exp.get("agents") or []:
        roots[a] = home / ".hermes" / "profiles" / f"aos-{a}"
    return roots


def snapshot_roots(exp, snap_dir):
    roots = {"front": snap_dir / "front", "home": snap_dir / "home"}
    # No `root:` — see live_roots(). A snapshot records profile trees and the household, not
    # the harness root, so a root: reference is skipped rather than failed here.
    for a in exp.get("agents") or []:
        roots[a] = snap_dir / a
    return roots


def resolve_ref(roots, ref):
    root, _, rest = ref.partition(":")
    if root not in roots:
        return None
    return roots[root] / rest if rest else roots[root]


def walk(directory):
    """Every file under `directory`, recursively. A missing directory yields nothing —
    the caller decides whether absence is a failure."""
    if directory is None:
        return
    directory = Path(directory)
    if not directory.exists():
        return
    for name in sorted(p.name for p in directory.iterdir()):
        abs_path = directory / name
        if abs_path.is_dir():
            yield from walk(abs_path)
        else:
            yield abs_path


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


class Checker:
    def __init__(self):
        self.failures = []

    def fail(self, code, msg):
        self.failures.append((code, msg))

    def run_expectations(self, exp_name, roots, live_mode=False):
        exp = yaml.safe_load((EXPECTATIONS / f"{exp_name}.yaml").read_text(encoding="utf-8"))

        for ref in exp.get("expect_files") or []:
            p = resolve_ref(roots, ref)
            if p is None or not p.exists():
                self.fail("golden/missing", f"{exp_name}: expected {ref}")
        for ref in exp.get("forbid_files") or []:
            p = resolve_ref(roots, ref)
            if p is not None and p.exists():
                self.fail("golden/forbidden",
                          f"{exp_name}: {ref} must not exist (used_by scoping)")
        for ref in exp.get("origin_tag_roots") or []:
            directory = resolve_ref(roots, ref)
            if directory is None:
                continue
            # Harness-owned bundled skills (seeded by `hermes profile create`, listed in the
            # profile's own .bundled_manifest) are pre-existing content, not aos artifacts —
            # the origin-tag rule applies to what the INSTALL materialized.
            bundled = set()
            manifest = directory / ".bundled_manifest"
            if manifest.exists():
                for line in manifest.read_text(encoding="utf-8").split("\n"):
                    name = line.split(":")[0].strip()
                    if name:
                        bundled.add(name)
            for f in walk(directory):
                if not f.name == "SKILL.md":
                    continue
                rel_parts = f.relative_to(directory).parts
                # aos materializes skills as top-level `<capability>-<id>/` dirs (cheat-sheet
                # rule); anything nested deeper is harness-owned category content. Bundled
                # names from the manifest are exempt either way.
                if len(rel_parts) != 2:
                    continue
                if rel_parts[0] in bundled or rel_parts[0] == ".hub":
                    continue
                # A referenced third-party skill (installed from vendor/, never rendered)
                # carries no origin tag by contract — it is not ours to modify.
                # `exp.vendored` names them.
                if rel_parts[0] in (exp.get("vendored") or []):
                    continue
                if not has_stamp(origin_stamp(f)):
                    self.fail("golden/origin-tag",
                              f"{exp_name}: {f} lacks {ORIGIN_FRONTMATTER_KEY}")
        for s in exp.get("schedules") or []:
            jobs_path = resolve_ref(roots, f"{s['profile']}:cron/jobs.json")
            found = False
            if jobs_path is not None and jobs_path.exists():
                try:
                    jobs = json.loads(jobs_path.read_text(encoding="utf-8")).get("jobs") or []
                    matches = [j for j in jobs
                               if str(j.get("name") or "").startswith(s["name_prefix"])]
                    found = len(matches) == 1   # single-owner: exactly one
                    if len(matches) > 1:
                        self.fail("golden/schedule-dup",
                                  f"{exp_name}: {s['name_prefix']} appears {len(matches)}× "
                                  f"(single-owner rule)")
                except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
                    self.fail("golden/jobs-parse", f"{exp_name}: {jobs_path}: {e}")
            if not found:
                self.fail("golden/schedule",
                          f"{exp_name}: no job named {s['name_prefix']}* in profile "
                          f"{s['profile']}")
        # The inverse of a sentinel: text an install must NOT write. A block we stopped
        # shipping has to be provably absent, or "we removed it" is only a claim.
        for s in exp.get("forbid_texts") or []:
            p = resolve_ref(roots, s["in"])
            if p is not None and p.exists():
                text = _read(p)
                if text is not None and s["text"] in text:
                    self.fail("golden/forbidden-text",
                              f'{exp_name}: "{s["text"]}" must not appear in {s["in"]}')
        for s in exp.get("sentinels") or []:
            if s.get("in"):
                p = resolve_ref(roots, s["in"])
                text = _read(p) if p is not None and p.exists() else None
                if text is None or s["text"] not in text:
                    self.fail("golden/sentinel",
                              f'{exp_name}: "{s["text"]}" not found in {s["in"]}')
            elif s.get("in_dir"):
                # A `root:` reference names the harness root (~/.hermes), which sits outside
                # every profile tree — so snapshots cannot contain it and the sentinel is
                # live-only. Skipping is right rather than failing: a snapshot that never
                # recorded the file cannot testify about it either way, and a permanent red
                # here would train people to ignore the gate.
                if not live_mode and s["in_dir"].startswith("root:"):
                    continue
                directory = resolve_ref(roots, s["in_dir"])
                found = False
                for f in walk(directory):
                    text = _read(f)
                    if text is not None and s["text"] in text:
                        found = True
                        break
                if not found:
                    self.fail("golden/sentinel",
                              f'{exp_name}: "{s["text"]}" not found anywhere under '
                              f'{s["in_dir"]}')
        # Symlink-install contract (§5.3): live trees must LINK harness skill dirs to the
        # pinned render in personal/ — snapshots dereference, so this is live-only.
        if live_mode:
            for ref in exp.get("expect_links") or []:
                p = resolve_ref(roots, ref)
                if p is None or not p.exists():
                    self.fail("golden/link-missing", f"{exp_name}: expected link {ref}")
                    continue
                if not p.is_symlink():
                    self.fail("golden/not-a-link",
                              f"{exp_name}: {ref} is not a symlink (copies are banned — §5.3)")
        if exp.get("lockfile_capabilities"):
            p = resolve_ref(roots, "home:.aos/installs.lock.yaml")
            if p is None or not p.exists():
                self.fail("golden/lockfile", f"{exp_name}: lockfile missing")
            else:
                lock_text = p.read_text(encoding="utf-8")
                for cap in exp["lockfile_capabilities"]:
                    if cap not in lock_text:
                        self.fail("golden/lockfile",
                                  f'{exp_name}: lockfile has no entry for "{cap}"')
                # Snapshots dereference symlinks, so the lockfile's `links` map is the only
                # deterministic residue of the symlink contract (§5.3) a committed tree can
                # carry.
                if exp.get("lockfile_links_into_personal"):
                    installs = (yaml.safe_load(lock_text) or {}).get("installs") or {}
                    for cap in exp["lockfile_capabilities"]:
                        links = (installs.get(cap) or {}).get("links") or {}
                        targets = list(links.values())
                        if not targets:
                            self.fail("golden/links",
                                      f"{exp_name}: {cap} records no links (copies are banned "
                                      f"— §5.3)")
                            continue
                        for t in targets:
                            # Renders live in personal/; a referenced third-party skill lives
                            # in vendor/ and is linked from there (never copied, never
                            # rendered).
                            if ("/personal/capabilities/" not in str(t)
                                    and "/vendor/" not in str(t)):
                                self.fail("golden/links",
                                          f"{exp_name}: {cap} link target neither a personal/ "
                                          f"render nor a vendor/ reference: {t}")

    # Canary check lives in the protocol, not here: re-run tests/golden/prestate.sh to a
    # A committed snapshot must equal what the normalizer produces — re-normalizing it is a
    # no-op. Without this, a snapshot updated by any path that skips the normalizer (a hand
    # edit, a re-render copied in) silently stops matching the pipeline, and the next real
    # re-snapshot shows a diff that reads as a change but isn't.
    # Descends through SKIP-named directories instead of normalizing them: the household root
    # is literally `home`, which the normalizer drops as harness runtime state.
    def check_normalization_is_idempotent(self, name, root):
        tmp = Path(tempfile.mkdtemp(prefix="aos-golden-"))
        try:
            for directory in normalizable_roots(root):
                rel = directory.relative_to(root)
                out = tmp / rel
                normalize_tree(directory, out)
                for file in walk(directory):
                    inner = file.relative_to(directory)
                    mirrored = out / inner
                    if not mirrored.exists():
                        self.fail("golden/normalize-drop",
                                  f"{name}: {rel}/{inner} does not survive re-normalization")
                    elif _read(file) != _read(mirrored):
                        self.fail("golden/normalize-idempotent",
                                  f"{name}: {rel}/{inner} is not what the normalizer "
                                  f"produces — re-run it through the normalizer")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def normalizable_roots(root):
    out = []
    for entry in sorted(p.name for p in Path(root).iterdir()):
        abs_path = Path(root) / entry
        if not abs_path.is_dir():
            continue
        if entry in SKIP:
            out.extend(normalizable_roots(abs_path))
        else:
            out.append(abs_path)
    return out


# second file and `diff` it against the pre-install one — byte-equal or the install
# touched something it must not.


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    live = "--live" in args
    names = [a for a in args if not a.startswith("--")]

    checker = Checker()
    if live:
        for name in (names or ["full-install"]):
            exp = yaml.safe_load((EXPECTATIONS / f"{name}.yaml").read_text(encoding="utf-8"))
            checker.run_expectations(name, live_roots(exp), True)
    else:
        snaps = sorted(p.name for p in GOLDEN_DIR.iterdir()) if GOLDEN_DIR.exists() else []
        for snap in snaps:
            exp_path = EXPECTATIONS / f"{snap}.yaml"
            if not exp_path.exists():
                continue
            exp = yaml.safe_load(exp_path.read_text(encoding="utf-8"))
            checker.run_expectations(snap, snapshot_roots(exp, GOLDEN_DIR / snap))
        for snap in snaps:
            if (EXPECTATIONS / f"{snap}.yaml").exists():
                checker.check_normalization_is_idempotent(snap, GOLDEN_DIR / snap)
        if not snaps:
            print("golden: no committed snapshots yet")
            return 0

    for code, msg in checker.failures:
        print(f"FAIL {code:<20} {msg}")
    print(f"golden: {len(checker.failures)} failures")
    return 1 if checker.failures else 0


if __name__ == "__main__":
    sys.exit(main())
