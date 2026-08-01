#!/usr/bin/env python3
# Does the template repo `kb init` clones still match the templates in this checkout?
#
# This gap bit twice in one session. `kb init` clones TEMPLATE_REPO_URL by default, but
# every test passes `--templates <local-dir>` to skip the network — so the entire suite
# can be green while the primary materialization path ships a stale contract file. The
# second time, the base's AGENTS.md was 30 lines longer than the kit's and still carried
# prose the rewrite existed to retire.
#
# Network-dependent by nature, so this is NOT part of `tools/check.sh` or CI: a gate that
# fails on a plane is a gate people learn to skip. Run it after touching
# capabilities/kb/skills/init/templates/, and before trusting a release.
#
# Usage: python -m aos_lint.gates.template_drift [--json]
# Exit 0 = in sync (or offline, reported as a skip), 1 = drift, 2 = could not check.

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..repo import REPO_ROOT

TEMPLATES = REPO_ROOT / "capabilities/kb/skills/init/templates"


def _walk(directory: Path, base=None) -> list[str]:
    base = base or directory
    out = []
    for p in sorted(directory.iterdir(), key=lambda p: p.name):
        if p.name == ".git":
            continue
        if p.is_dir():
            out.extend(_walk(p, base))
        else:
            out.append(str(p.relative_to(base)))
    return out


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in args

    # The URL the tool actually clones — read from the tool, never duplicated here, or this
    # check drifts from the thing it is checking.
    constants = (REPO_ROOT / "capabilities/kb/tool/src/aos_kb/constants.py").read_text(
        encoding="utf-8")
    m = re.search(r"^TEMPLATE_REPO_URL\s*=\s*[\"'](.+?)[\"']", constants, re.M)
    if not m:
        print("could not find TEMPLATE_REPO_URL in the tool constants", file=sys.stderr)
        return 2
    url = m.group(1)

    tmp = Path(tempfile.mkdtemp(prefix="aos-tpl-"))
    clone = tmp / "template"
    try:
        try:
            subprocess.run(["git", "clone", "-q", "--depth", "1", url, str(clone)],
                           capture_output=True, check=True)
        except (subprocess.CalledProcessError, OSError) as e:
            detail = getattr(e, "stderr", None) or str(e)
            if isinstance(detail, bytes):
                detail = detail.decode(errors="replace")
            first = str(detail).strip().split("\n")[0]
            msg = f"could not clone {url} — offline? ({first})"
            if as_json:
                print(json.dumps({"status": "skipped", "reason": msg}))
            else:
                print(f"template drift: SKIPPED — {msg}")
            return 0   # offline is not a failure; this check is advisory by design

        drift = []
        for rel in _walk(TEMPLATES):
            mine = (TEMPLATES / rel).read_text(encoding="utf-8")
            theirs_path = clone / rel
            theirs = theirs_path.read_text(encoding="utf-8") if theirs_path.exists() else None
            if theirs is None:
                drift.append({"file": rel, "why": "missing from the template repo"})
            elif theirs != mine:
                drift.append({"file": rel, "why": "differs from this checkout"})
        # The template repo's own README describes the repo and is deliberately NOT a template
        # (base.README.md is the one that renders into a base), so it is not expected here.
        extra = [r for r in _walk(clone) if r != "README.md" and not (TEMPLATES / r).exists()]
        for rel in extra:
            drift.append({"file": rel,
                          "why": "in the template repo but not in this checkout"})

        if as_json:
            print(json.dumps({"status": "drift" if drift else "in-sync", "url": url,
                              "drift": drift}, indent=2))
        elif drift:
            print(f"template drift: {len(drift)} file(s) out of sync with {url}\n",
                  file=sys.stderr)
            for d in drift:
                print(f"  {d['file']}: {d['why']}", file=sys.stderr)
            print("\nA default `kb init` clones that repo, so users get the repo's version,",
                  file=sys.stderr)
            print("not this checkout's. Push the templates, or explain the divergence.",
                  file=sys.stderr)
        else:
            print(f"template drift: in sync with {url}")
        return 1 if drift else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
