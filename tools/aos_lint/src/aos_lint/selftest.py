#!/usr/bin/env python3
"""Selftest: every lint check must fire at least once on the planted-violation fixture.
Guards against checks silently rotting into no-ops.

Usage: python -m aos_lint.selftest
"""

import sys
from pathlib import Path

from .checks import SELFTEST
from .context import build_context

# The fixture stays where it is (tools/lint/selftest/fixture) across the port: it is a tree of
# planted violations, and moving it would have made the port's own diff unreadable — every
# finding's `file` carries the path.
ROOT = Path(__file__).resolve().parents[4] / "tools/lint/selftest/fixture"

EXPECTED = [
    "manifest/unknown-key", "manifest/id", "manifest/version", "manifest/tags",
    "manifest/summary", "manifest/readme", "manifest/mod-example",
    "depends/capability", "depends/host-feature", "depends/host-level",
    "schedules/unknown-key", "schedules/id", "schedules/cron", "schedules/agent",
    "schedules/prompt-ref", "schedules/degraded",
    "skills/unknown-key", "skills/missing-dir", "skills/undeclared",
    "skill/no-cross-path",
    "skill/origin-tag", "skill/unknown-key", "skill/name", "skill/description",
    "skill/used-by", "skill/used-by-ref",
    # §2.5 skill identity: the installed name is what ships, so it carries the limits
    "skills/prefix-format", "skills/prefix-redundant", "skills/installed-name",
    "skills/installed-collision", "skills/ref-unqualified",
    # ...and its mirror: the computed name written literally, plus a slot that resolves to
    # nothing. Both are what a prefix rename silently invalidated with green CI.
    "skills/ref-hardcoded", "skills/ref-dangling", "agents/ref-dangling",
    # Agent Skills authoring conformance
    "skill/reserved-word", "skill/xml-tags", "skill/nested-reference", "skill/reference-toc",
    "skill/description-person",
    "skill/package-path", "skill/foreign-reference",
    "agent/unknown-key", "agent/required", "agent/name-file", "agent/model-class",
    "agent/tool", "agent/workspace", "agent/context-file",
    "onboarding/unknown-key", "onboarding/required", "onboarding/duplicate-id",
    "onboarding/type", "onboarding/flag",
    "overlay/shipped", "overlay/state-dir", "overlay/answer-key", "overlay/answer-missing",
    "overlay/secret-ref",
    "refs/dead",
    "cheatsheet/section", "structure/harnesses-dir",
    "secrets/token", "secrets/jwt", "secrets/phone", "secrets/whatsapp-jid",
    "kb/zone-key", "kb/owner-agent",
    # §2.2's degenerate case, and it is EXPECTED rather than tolerated: the check only fires
    # where an alternative existed (an agent or a schedule to scope to), so nothing else in
    # this fixture can plant it — prefix-cap carries a `janitor` agent for exactly this.
    "skill/all-main",
]

REFER_REL = "capabilities/name-cap/skills/refer/SKILL.md"


def main(argv=None) -> int:
    ctx = build_context(ROOT)
    for check in SELFTEST:
        check(ctx)
    findings = ctx.findings
    fired = {f.code for f in findings}

    # the cheat-sheet section check must fire on the sanctioned shape (a reference file of the
    # skill that reads it) AND on the retired capability-level layout, which must not go
    # silently unchecked while it still exists in the wild
    cheat_files = {f.file for f in findings if f.code == "cheatsheet/section"}
    for want in ["harnesses/badharness.md",
                 "skills/capture/reference/harness-badharness.md",
                 "capabilities/half-cap/harnesses/stale.md"]:
        if not any(f.endswith(want) for f in cheat_files):
            print(f"selftest FAILED — cheatsheet/section did not fire on {want}",
                  file=sys.stderr)
            return 1

    # skill/all-main must fire where a role EXISTED to scope to and was ignored, and must stay
    # silent where there was never an alternative. Both halves are pinned by file, because the
    # code firing at all proves nothing: `name-cap` is five main-only skills with no agents, so
    # a check that ignored the role question entirely would still light this code up.
    all_main_files = {f.file for f in findings if f.code == "skill/all-main"}
    if not any("prefix-cap" in f for f in all_main_files):
        print("selftest FAILED — skill/all-main did not fire on prefix-cap, which scopes "
              "every skill to main while declaring a `janitor` agent", file=sys.stderr)
        return 1
    for quiet in ("name-cap", "half-cap"):
        if any(quiet in f for f in all_main_files):
            print(f"selftest FAILED — skill/all-main fired on {quiet}, which declares no agent "
                  "and no schedule: there was no role to scope to, so the question is "
                  "unanswerable rather than unanswered", file=sys.stderr)
            return 1

    # The slot checks must fire on a dangling slot and stay SILENT on an escaped one. Pinned by
    # line, because the codes firing at all proves nothing: the same fixture line carries both
    # forms, so a check that ignored the `(?<!\\)` guard would light the codes up identically
    # while failing every doc that TEACHES the syntax — starting with reference/naming.md. The
    # line is located by content rather than numbered, so editing the fixture cannot quietly
    # aim this assertion at a blank line.
    refer_lines = (ROOT / REFER_REL).read_text(encoding="utf-8").split("\n")
    escaped_line = next((i + 1 for i, line in enumerate(refer_lines)
                         if "escaped example" in line), 0)
    if not escaped_line:
        print(f"selftest FAILED — {REFER_REL} no longer carries the escaped-slot line the "
              "negative assertion is about", file=sys.stderr)
        return 1
    slot_findings = [f for f in findings if f.code.endswith("/ref-dangling")]
    on_escaped = [f for f in slot_findings if f.file == f"{REFER_REL}:{escaped_line}"]
    if on_escaped:
        joined = "\n  ".join(f.message for f in on_escaped)
        print(f"selftest FAILED — {len(on_escaped)} ref-dangling finding(s) on {REFER_REL}:"
              f"{escaped_line}, the escaped-slot line: \\{{{{skill: …}}}} is invisible to "
              f"render, so it must be invisible to lint too\n  {joined}", file=sys.stderr)
        return 1
    for code, want in [("skills/ref-dangling", "{{skill: kapture}}"),
                       ("agents/ref-dangling", "{{agent: ghost}}")]:
        if not any(f.code == code and want in f.message for f in slot_findings):
            print(f"selftest FAILED — {code} did not fire on the unescaped {want}",
                  file=sys.stderr)
            return 1

    missing = [code for code in EXPECTED if code not in fired]
    unexpected = [code for code in sorted(fired)
                  if code not in EXPECTED and not code.startswith("structure/")
                  and code != "skill/description-when" and code != "skill/name-dir"]

    if missing:
        joined = "\n  ".join(missing)
        print(f"selftest FAILED — checks that never fired on the fixture:\n  {joined}",
              file=sys.stderr)
    if unexpected:
        joined = "\n  ".join(unexpected)
        print(f"selftest NOTE — codes fired that the contract does not list (add or fix):\n"
              f"  {joined}", file=sys.stderr)
    print(f"lint selftest: {len(fired)} distinct codes fired, {len(missing)} expected codes "
          f"missing")
    return 1 if (missing or unexpected) else 0


if __name__ == "__main__":
    sys.exit(main())
