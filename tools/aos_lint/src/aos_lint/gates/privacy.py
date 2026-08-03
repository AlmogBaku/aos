#!/usr/bin/env python3
# The privacy gate: no personal-environment literal survives anywhere in the tracked tree.
#
# This repo is public and its capabilities are extracted from a live private setup, so
# CONTRIBUTING.md and AGENTS.md both require that nothing personal lands in a committed file.
# That was care rather than a gate, and care lost: a maintainer's home directory reached 22
# transcripts (98 paths, plus a numeric uid, a session uuid and a private KB's mtime), their
# `<user>@<host>.local` principal reached a COMMITTED golden snapshot, and their legacy KB path
# reached two normative rules that then read as universal. None of it was noticed by anything.
#
# The rule is a SHAPE, deliberately. A gate whose ban list named the maintainer would move the
# leak from the tree into this file, and would say nothing about the next contributor's
# username. So this bans absolute home paths, synthesized hostname principals, session ids and
# per-uid scratch paths — whoever they belong to — and exempts the names that are placeholders
# by convention. What it deliberately does NOT check is real NAMES: a shape gate cannot
# recognise a person's name without containing it, so names stay with CONTRIBUTING.md's scrub
# checklist and human review.
#
# Why a gate and not a lint check, given `checks/` is where a per-file rule would normally go:
#
#   - The exemption policies are OPPOSITES. `gates.retired` must exempt tests/transcripts/,
#     because retired vocabulary is historical and a record that named today's world would not
#     be a record. Privacy must NOT: verbatimness is a policy about vocabulary, and the
#     public-repo redaction rule has no historical exemption. One module cannot hold both
#     policies without a per-concern split inside its allowlist.
#   - `checks/` is bounded by ctx.files, whose SKIP_PREFIXES deliberately blinds it to the
#     lint selftest's fixture — while `selftest` would then require every code here to fire
#     inside that same fixture. That is a structural contradiction, not a preference.
#   - docs/TESTING.md states the split: the linter validates schema, gates check content.
#     "Is there somebody's home directory in this file" is content, over arbitrary files —
#     including the .log transcripts, which belong to no capability at all.
#
# Usage: python -m aos_lint.gates.privacy [relPathPrefix ...]
#   With prefixes, only matching files are checked. A prefix matching nothing is an ERROR,
#   not a pass — same semantics as gates.retired, for the same reason.
#
# Note walk_repo does not read .gitignore, so an untracked scratch file is scanned like any
# other. That is useful here: planting one literal of each shape in a scratch file is how you
# prove this gate is not vacuous.

import re
import sys

from ..repo import REPO_ROOT, walk_repo

# Names that are placeholders by convention, so a path naming one identifies nobody. This is
# the ONLY allowlist this gate has — after the redaction sweep it needs no path exemptions at
# all, which is the difference between banning a shape and banning a vocabulary.
GENERIC = {
    "user", "users", "you", "youruser", "your-user", "username", "someuser",
    "runner", "me", "someone", "somebody", "anyone", "example", "sample",
    "alice", "bob", "carol", "dana", "eve", "dev", "developer", "fixture",
    "host", "hostname", "localhost", "name", "test", "tester", "ci", "agent",
}

# Each entry: code, pattern, the group indices holding a NAME (checked against GENERIC —
# empty means the shape alone is the violation), and what to say.
PATTERNS = [
    ("privacy/home-path",
     # Not preceded by a word char, dot, dollar, quote, slash or dash — so `$HOME/...`,
     # `<HOME>/...`, `~/...` and `profiles/aos-test/home/...` are all untouched. The ban is
     # on an ABSOLUTE path naming a person, not on the word "home".
     re.compile(r"(?<![\w.$'\"/-])/(?:home|Users)/([A-Za-z_][A-Za-z0-9_.-]*)"),
     (1,),
     "an absolute path inside somebody's home directory — write `~/` or `<HOME>/`"),
    ("privacy/mangled-home",
     # Tooling that flattens a path into a filename rewrites / to -, producing
     # `-home-<name>-...`. A plain /home/<name> sweep does not see this form, which is
     # precisely how one survived a redaction pass.
     re.compile(r"(?<![A-Za-z0-9])-(?:home|Users)-([A-Za-z0-9_.]+)"),
     (1,),
     "a home directory flattened into a filename, which a plain /home/<name> sweep misses"),
    ("privacy/weak-principal",
     # `aos_kb.identity.synthesize_principal` builds <user>@<host>.local from getpass and
     # socket. Both halves are facts about the operator. Angle-bracket placeholders
     # (`<user>@<host>.local`) fall outside the character class and so pass, which is what
     # lets the docs teaching this rule state the shape.
     re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9-]+)\.local\b"),
     (1, 2),
     "a synthesized <user>@<host>.local principal — two facts about the operator, and "
     "`is_weak_principal` exists because it should never author a write"),
    ("privacy/session-id",
     re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
     (),
     "a session/run uuid — identifies one run on one machine"),
    ("privacy/uid-path",
     re.compile(r"(?<![\w-])/(?:tmp|run|var/folders)/[A-Za-z][A-Za-z0-9_.-]*?-(\d{3,6})"
                r"(?=[/\s`'\"]|$)"),
     (),
     "a numeric uid in a per-user temp path"),
]

# The selftest's job, done in-file. A `gates/` code is invisible to aos_lint.selftest, whose
# EXPECTED list is derived from checks/ — so a pattern that rotted into a no-op would report
# `clean` forever, which is the exact failure mode this gate exists to prevent elsewhere.
#
# Built by CONCATENATION so the canaries do not match the patterns as this file's own source
# text. That is why, unlike gates.retired, this gate needs no exemption for its own path — and
# if a formatter ever joins these literals, the gate fails ON ITSELF, loudly, rather than
# quietly exempting itself.
CANARIES = [
    ("privacy/home-path", "/home/" + "jdoe/notes.md"),
    ("privacy/mangled-home", "/tmp/x/-home-" + "jdoe-proj/y"),
    ("privacy/weak-principal", "jdoe@" + "jdoe-laptop" + ".local"),
    ("privacy/session-id", "af74abc6-b33e-45a6" + "-8fb7-afa4f12fd282"),
    ("privacy/uid-path", "/tmp/claude-" + "1002/scratch"),
]

# Every text form a leak has actually taken. `.log` is load-bearing: 25 of the transcripts are
# .log files, and they carried three of the five leaks this gate was written for — while
# checks/secrets.py's own extension list omits .log, so nothing had ever scanned them.
TEXT_EXT = re.compile(
    r"\.(md|ya?ml|json|mjs|js|py|sh|txt|tmpl|log|svg|toml|cfg|ini)$"
    r"|(?:^|/)(?:LICENSE|Makefile|Dockerfile)$")


def _findings(text: str):
    """Every (code, matched-text, message) in `text`, generically-named paths excluded."""
    for code, pattern, name_groups, what in PATTERNS:
        for m in pattern.finditer(text):
            if any(m.group(g).lower() in GENERIC for g in name_groups):
                continue
            yield code, m.group(0), what


def main(argv=None) -> int:
    prefixes = list(sys.argv[1:] if argv is None else argv)
    failures: list[str] = []
    matched: set[str] = set()

    # Self-proof first: a rotted pattern must fail here rather than sail through the walk.
    for code, canary in CANARIES:
        if not any(c == code for c, _, _ in _findings(canary)):
            failures.append(f"{__name__}: pattern {code} no longer matches its own canary — "
                            f"the rule has rotted into a no-op")

    for rel in walk_repo(REPO_ROOT):
        if not TEXT_EXT.search(rel):
            continue
        if prefixes:
            hit = next((p for p in prefixes if rel.startswith(p)), None)
            if hit is None:
                continue
            matched.add(hit)
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for code, found, what in _findings(text):
            failures.append(f'{rel}: {code} — {what}: "{found}"')

    for p in prefixes:
        if p not in matched:
            failures.append(f"{p}: prefix matched no file — check the path")

    if failures:
        print(f"privacy gate: {len(failures)} failure(s)\n", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    suffix = f" ({' '.join(prefixes)})" if prefixes else ""
    print(f"privacy gate: clean{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
