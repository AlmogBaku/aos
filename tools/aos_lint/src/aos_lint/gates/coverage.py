#!/usr/bin/env python3
# Two mechanical coverage checks, so the docs cannot quietly fall behind the tools.
#
#   1. every CLI verb appears in docs/USAGE.md and AGENTS.md's verb list
#   2. every count quoted in docs/TESTING.md matches what the tools actually report
#
# Why mechanical: the CLI grew by eight verbs in one pass and the docs did not, and
# docs/TESTING.md claimed "85 checks in 14 code families" while the linter emitted 81 in 13.
# Neither is a mistake anyone makes on purpose — they are what happens when a number lives in
# prose and its source lives in code. Both checks derive the truth from the tool rather than
# from a second hand-maintained list, so there is nothing to keep in sync.
#
# AGENTS.md, not CLAUDE.md: the latter is a symlink to the former (one source, two names), so
# reading both would check the same bytes twice and reading only CLAUDE.md would hide that.
#
# Usage: python -m aos_lint.gates.coverage
#   Requires `uv` to interrogate the tool's own --help. Skips with a note if absent — the same
#   shape as check.sh's tier-0 guard, so a machine without uv reports honestly instead of green.

import re
import shutil
import subprocess
import sys

from ..repo import REPO_ROOT, list_capabilities, walk_repo

# The lint's own check inventory lives in its check MODULES, the way it lived in
# tools/lint/checks/*.mjs before the port.
CHECK_PKG = "tools/aos_lint/src/aos_lint/checks/"
# version/* is emitted by the diff-aware pass. It is inside the package now (it always was a
# check), so unlike the .mjs version there is no second file to scan — but the entry point is
# still read, in case a code is ever reported from the driver rather than from a check.
CLI_REL = "tools/aos_lint/src/aos_lint/cli.py"


def main(argv=None) -> int:
    failures: list[str] = []

    def read(rel):
        return (REPO_ROOT / rel).read_text(encoding="utf-8")

    def fail(where, msg):
        failures.append(f"{where}: {msg}")

    uv = shutil.which("uv") is not None

    # ---- 1. verb coverage ----------------------------------------------------------------
    # Parsed from the CLI's own --help, so the list cannot drift from the implementation.
    if not uv:
        print("coverage gate: verb coverage SKIPPED (uv not found — install: "
              "https://docs.astral.sh/uv/)")
    else:
        help_text = subprocess.run(
            ["uv", "run", "--quiet", "--project", "capabilities/kb/tool", "kb", "--help"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        block = help_text[help_text.index("Commands:"):]
        verbs = re.findall(r"^\s{2}(\S+)\s{2,}", block, re.M)
        if len(verbs) < 20:
            fail("kb --help",
                 f"parsed only {len(verbs)} verbs from the Commands block — the parser has "
                 f"drifted from typer's output format, and a coverage check that sees no "
                 f"verbs passes vacuously")
        for doc in ["docs/USAGE.md", "AGENTS.md"]:
            text = read(doc)
            missing = [v for v in verbs if not re.search(rf"\b{re.escape(v)}\b", text)]
            if missing:
                fail(doc, f"{len(missing)} CLI verb(s) undocumented: {' '.join(missing)}")

    # ---- 2. quoted counts ---------------------------------------------------------------
    # A number in prose is a claim about the tools. Check it against them.
    testing = read("docs/TESTING.md")

    # The linter's own check inventory: every code it can emit, and the families they group
    # into. Every `family/code` string a check module mentions — NOT only the ones passed
    # literally to report(). checks/secrets.py defines its five codes in a table and reports
    # them through a variable (`ctx.report("error", code, …)`), so a literal-argument regex
    # saw ZERO of them: the prose said 81/13 and this gate derived 81/13, both wrong by the
    # same five. A derived count agreeing with a wrong number is the one failure a derived
    # count is supposed to make impossible, so it matches the code strings themselves and
    # lets the selftest — which pins every code by name — be the check that they are all
    # really reachable.
    codes = set()
    for rel in walk_repo(REPO_ROOT):
        if not rel.startswith(CHECK_PKG) or not rel.endswith(".py"):
            continue
        codes |= set(re.findall(r"\"([a-z]+/[a-z][a-z-]*)\"", read(rel)))
    codes |= set(re.findall(r"\"([a-z]+/[a-z][a-z-]*)\"", read(CLI_REL)))
    # `lint/crash` is the driver's own panic path, not a contract check — the .mjs gate never
    # counted it because it lived outside checks/, and the number in the docs is about the
    # checks. Excluded explicitly rather than by accident of file layout.
    codes.discard("lint/crash")
    families = {c.split("/")[0] for c in codes}

    claim = re.search(r"\((\d+) checks in (\d+) code families", testing)
    if not claim:
        fail("docs/TESTING.md",
             'no "(N checks in M code families" claim found — if the sentence was reworded, '
             "update this check rather than dropping it")
    else:
        if int(claim.group(1)) != len(codes):
            fail("docs/TESTING.md",
                 f"claims {claim.group(1)} checks; the linter emits {len(codes)} distinct codes")
        if int(claim.group(2)) != len(families):
            fail("docs/TESTING.md",
                 f"claims {claim.group(2)} code families; there are {len(families)} "
                 f"({' '.join(sorted(families))})")

    # Suite sizes, if the doc quotes them. `unittest` prints "Ran N tests" to stderr.
    if uv:
        for suite, label in [("tests/tool/test_kb.py", "test_kb.py"),
                             ("tests/tool/test_cap.py", "test_cap.py")]:
            # Only if the doc quotes a size. It does not today, so this whole block is dormant
            # — deliberately, because a suite size in prose is a number that rots weekly and
            # the count is already visible in every test run. It stays wired so that quoting
            # one is safe.
            quoted = re.search(rf"{re.escape(label)}[^\n]*?\b(\d+) tests", testing)
            if not quoted:
                continue
            # unittest prints "Ran N tests" to STDERR, and passes without throwing — so the
            # stream has to be captured explicitly. Piping stdout to the parent would leak the
            # dots into this gate's own output, hence the pipe on both.
            res = subprocess.run(["uv", "run", "--quiet", suite], cwd=REPO_ROOT,
                                 capture_output=True, text=True)
            ran = re.search(r"Ran (\d+) tests", f"{res.stdout}{res.stderr}")
            if ran and int(quoted.group(1)) != int(ran.group(1)):
                fail("docs/TESTING.md",
                     f"claims {label} has {quoted.group(1)} tests; it has {ran.group(1)}")

    # The installed-skill count, wherever prose states one. `aos-cap skills` is the authority,
    # and the same number appears in README support tables and the golden expectations.
    # Scoped to the `skills:` block. A bare `/^\s+- id:/` also matched `schedules[]` and
    # `kb.zones[]` entries, so it reported 26 where `aos-cap skills` — the authority this claim
    # is about — reports 22. Nothing quotes the number today, which is exactly when a wrong
    # check is cheapest to fix.
    skill_count = 0
    for cap in list_capabilities(REPO_ROOT):
        block = re.search(r"^skills:\n((?:[ \t]+.*\n|\n)*)", read(f"{cap.rel}/CAPABILITY.md"),
                          re.M)
        skill_count += len(re.findall(r"^\s+- id:", block.group(1), re.M)) if block else 0
    for doc in ["docs/TESTING.md", "README.md"]:
        m = re.search(r"\b(\d+) installed skills?\b", read(doc))
        if m and int(m.group(1)) != skill_count:
            fail(doc, f"claims {m.group(1)} installed skills; the manifests declare "
                      f"{skill_count}")

    # 3. MOD.example.md's `onboarded_version` must match its own capability's version. It is
    # the shipped seed of the field that governs re-ask behaviour, and a version bump that
    # misses it ships a seed claiming the user onboarded on a release that never existed.
    # Found by review rather than by any gate, which is why it is one now.
    for cap in list_capabilities(REPO_ROOT):
        seed_rel = f"{cap.rel}/MOD.example.md"
        try:
            seed = read(seed_rel)
        except OSError:
            continue     # the pair is optional (§2.1)
        declared = re.search(r"^version:\s*(\S+)", read(f"{cap.rel}/CAPABILITY.md"), re.M)
        seeded = re.search(r"^onboarded_version:\s*(\S+)", seed, re.M)
        if declared and seeded and declared.group(1) != seeded.group(1):
            fail(seed_rel, f"onboarded_version {seeded.group(1)} but the capability is "
                           f"{declared.group(1)}")

    if failures:
        print(f"coverage gate: {len(failures)} failure(s)\n", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"coverage gate: clean ({len(codes)} lint codes in {len(families)} families)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
