#!/usr/bin/env python3
"""Tier-1 deterministic lint (RFC-002). Blocking: exits non-zero on any error.

Usage: aos-lint [--base <ref>] [--root <dir>]

Deliberately argparse and not typer: this is repo-side tooling, not a shipped capability
tool, so it carries no dependency the kit's own CI would have to install for two flags.
"""

import argparse
import sys
import traceback
from pathlib import Path

from .checks import ALL
from .context import build_context
from .repo import REPO_ROOT
from .sortkey import locale_key


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="aos-lint", add_help=True)
    parser.add_argument("--base", default=None,
                        help="git ref to diff against; enables the version-bump check")
    # --root lints a tree other than this checkout — capability-build points it at the
    # user's personal root so a freshly built package is actually linted (not the kit).
    parser.add_argument("--root", default=None, help="lint a tree other than this checkout")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else REPO_ROOT
    # Linting a root other than this checkout means linting a user's personal root
    # (capability-build's post-build gate): the overlay family lives there legitimately,
    # dependencies may resolve into the kit, and the kit's git history says nothing about it.
    personal_root = root != REPO_ROOT

    ctx = build_context(
        root,
        # version-bump diffs the kit's history, not a personal root's
        base=None if personal_root else args.base,
        personal_root=personal_root,
        dep_roots=[REPO_ROOT] if personal_root else [],
    )

    for check in ALL:
        try:
            check(ctx)
        except Exception:
            ctx.report("error", "lint/crash", check.__name__, traceback.format_exc())

    ctx.findings.sort(key=lambda f: (locale_key(f.file), locale_key(f.code)))
    for f in ctx.findings:
        label = "ERROR" if f.severity == "error" else "WARN "
        print(f"{label} {f.code:<24} {f.file}: {f.message}")
    errors = sum(1 for f in ctx.findings if f.severity == "error")
    warns = len(ctx.findings) - errors
    print(f"\naos-lint: {len(ctx.caps)} capabilities, {errors} errors, {warns} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
