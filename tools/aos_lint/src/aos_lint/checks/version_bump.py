import re
import subprocess

from ..frontmatter import read_frontmatter
from ..repo import REPO_ROOT

_VERSION = re.compile(r"^version:\s*[\"']?([\d.]+)", re.M)


# design/install-flow.md §3: upgrades key off version; CI requires a bump when
# a capability's files change. Diff-aware — runs only with --base.
def check_version_bumps(ctx) -> None:
    if not ctx.base:
        return
    try:
        out = subprocess.run(["git", "diff", "--name-only", f"{ctx.base}...HEAD"],
                             cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, OSError):
        ctx.report("warn", "version/base", ".",
                   f'cannot diff against "{ctx.base}" — skipping version-bump check')
        return
    changed = [line for line in out.split("\n") if line]
    for cap in ctx.caps:
        if not any(f.startswith(f"{cap.rel}/") for f in changed):
            continue
        current = (read_frontmatter(cap.dir / "CAPABILITY.md").data or {}).get("version")
        try:
            old = subprocess.run(
                ["git", "show", f"{ctx.base}:{cap.rel}/CAPABILITY.md"],
                cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        except (subprocess.CalledProcessError, OSError):
            continue  # capability is new in this diff — no bump needed
        m = _VERSION.search(old.split("\n---")[0])
        previous = m.group(1) if m else None
        if previous and str(current) == previous:
            ctx.report("error", "version/bump", f"{cap.rel}/CAPABILITY.md",
                       f"files changed vs {ctx.base} but version stayed {current} "
                       f"(install-flow §3)")
