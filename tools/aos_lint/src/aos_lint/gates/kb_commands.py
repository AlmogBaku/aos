#!/usr/bin/env python3
# Every `kb <verb> --flag` the kb capability's prose names must exist in the tool.
#
# Why this is a script and not a careful read: the LAYOUT 2 rewrite was reviewed twice by
# hand, and both passes still missed documented commands that fail on invocation — a verb
# spelled as a positional when it is an option, a required flag omitted, a flag deleted from
# the tool but still advertised. The failure mode is uniform: the agent runs what the skill
# says, the tool exits non-zero or silently does the wrong thing, and nothing in CI noticed
# because the prose is just markdown. A verb/flag extractor closes that class mechanically.
#
# What it does NOT check: whether the *semantics* match (that `inbox` is agent-scoped, that
# prune resolves a base by walking parents). Those need a human or a test. This only proves
# that every command named is a command that exists, with flags that exist.
#
# Usage: python -m aos_lint.gates.kb_commands
#   Requires `uv` to interrogate the tool's own --help. Skips with a note if absent, the
#   same shape as check.sh's tier-0 guard.

import re
import shutil
import subprocess
import sys

from ..repo import REPO_ROOT, walk_repo

CAP = "capabilities/kb"
# Any capability whose prose invokes `kb` is in scope, not just the one that ships the
# tool: work-tracker composes with kb ONLY through this command on PATH (RFC-009 keeps
# cross-capability skill references out), so its skills carry real invocations with no
# other check on them. A documented command that fails on invocation is the same defect
# wherever it is written.
# Plus the human-facing docs, which are just as able to document a command that fails on
# invocation — and more likely to be trusted, since a person types from them directly. Nine
# commands in the capability prose failed on invocation after two careful human passes; there
# is no reason docs/ would be different, and no reason to find out the expensive way.
SCOPES = [CAP, "capabilities/work-tracker", "docs/", "README.md", "AGENTS.md",
          "BOOTSTRAP.md", "CONTRIBUTING.md"]
TOOL = REPO_ROOT / "capabilities/kb/tool"

# Prose writes commands inside backticks, sometimes wrapped across lines. Normalise
# whitespace so a wrapped invocation still parses as one command.
CMD_RE = re.compile(r"`kb\s+([^`]+)`")
_FLAG_RE = re.compile(r"(--[a-z][a-z0-9-]*)")
_VERB_LINE = re.compile(r"^\s{2,}([a-z][a-z-]*)\s{2,}\S")
_NEGATED = re.compile(r"\b(?:no|not a|never)\s*$", re.I)
_WS = re.compile(r"\s+")


def _help(args):
    try:
        return subprocess.run(
            ["uv", "run", "--quiet", "--project", str(TOOL), "kb", *args, "--help"],
            capture_output=True, text=True, check=True,
            stdin=subprocess.DEVNULL).stdout
    except (subprocess.CalledProcessError, OSError):
        return None


def _flags_of(text):
    return set(_FLAG_RE.findall(text))


# Two shapes carry a verb's operations. Typer subcommands show up under `Commands:`
# (`kb pending add`), while some verbs take the op as an enumerated positional instead
# (`kb state {op}:<add|bump|drop|check|show>`). Both are "kb <verb> <op>" to a reader, so
# both have to be validated, or a typo in the second shape sails through.
def _subs_of(text):
    out = set()
    if "Commands:" in text:
        block = text[text.index("Commands:"):]
        for line in block.split("\n")[1:]:
            m = _VERB_LINE.match(line)
            if m:
                out.add(m.group(1))
    usage = re.search(r"^Usage:.*$", text, re.M)
    if usage:
        enumerated = re.search(r"<([a-z|-]+\|[a-z|-]+)>", usage.group(0))
        if enumerated:
            out |= set(enumerated.group(1).split("|"))
    return out


def main(argv=None) -> int:
    if shutil.which("uv") is None:
        print("kb command check: SKIPPED (uv not found — install: "
              "https://docs.astral.sh/uv/)")
        return 0

    # Parse `kb --help` for the verb list, then each verb's own --help for its flags and
    # whether it takes positional arguments.
    root_help = _help([])
    if not root_help:
        print("kb command check: could not run `kb --help` — is the tool installable?",
              file=sys.stderr)
        return 1

    verbs = {}   # verb -> {flags, subcommands, sub}
    commands_block = root_help[root_help.index("Commands:"):]
    for line in commands_block.split("\n")[1:]:
        m = _VERB_LINE.match(line)
        if m:
            verbs[m.group(1)] = None

    for verb in list(verbs):
        text = _help([verb])
        if text is None:
            verbs[verb] = {"flags": set(), "subcommands": set(), "sub": {}}
            continue
        subcommands = _subs_of(text)
        entry = {"flags": _flags_of(text), "subcommands": subcommands, "sub": {}}
        for s in subcommands:
            st = _help([verb, s])
            entry["sub"][s] = set() if st is None else _flags_of(st)
        verbs[verb] = entry

    # Global options live on the root and are legal after `kb` before any verb.
    global_flags = _flags_of(root_help[:root_help.index("Commands:")])

    failures = []
    for rel in walk_repo(REPO_ROOT):
        if not any(rel == s or rel.startswith(s if s.endswith("/") else f"{s}/")
                   for s in SCOPES):
            continue
        if rel.startswith(f"{CAP}/tool/"):
            continue      # the tool documents itself
        if rel == "docs/BUILD-GAPS.md":
            continue      # append-only rows quote commands as they were
        if not rel.endswith(".md") and not rel.endswith(".yaml"):
            continue
        abs_path = REPO_ROOT / rel
        if not abs_path.exists():
            continue
        text = abs_path.read_text(encoding="utf-8")

        for m in CMD_RE.finditer(text):
            raw = _WS.sub(" ", m.group(1)).strip()
            # Prose sometimes names a verb precisely to say it does NOT exist ("There is no
            # `kb promote` verb"). That is the correct thing to document, so honour the
            # negation rather than forcing the sentence to avoid the backticks.
            before = text[max(0, m.start() - 40):m.start()]
            if _NEGATED.search(before):
                continue
            # Placeholders and prose fragments: `kb <verb>`, `kb --help`, `kb capture|set`.
            if raw[:1] in ("<", "|") or "|" in raw:
                continue
            tokens = raw.split(" ")
            i = 0
            # skip global options (and their values) that precede the verb
            while i < len(tokens) and tokens[i].startswith("-"):
                flag = tokens[i].split("=")[0]
                if flag not in global_flags:
                    failures.append(f'{rel}: `kb {raw}` — "{flag}" is not a global option')
                i += 1 if "=" in tokens[i] else 2   # assume `--flag value`
            if i >= len(tokens):
                continue
            verb = tokens[i]
            if verb[:1] in ("<", "{"):
                continue                            # `kb <verb> …` placeholder
            if verb not in verbs:
                failures.append(f'{rel}: `kb {raw}` — no such verb "{verb}"')
                continue
            entry = verbs[verb]
            rest = tokens[i + 1:]
            # a subcommand, if this verb has them and the next token names one
            flag_set = entry["flags"]
            if entry["subcommands"] and rest and not rest[0].startswith("-"):
                if rest[0] in entry["subcommands"]:
                    flag_set = entry["flags"] | entry["sub"].get(rest[0], set())
                    rest = rest[1:]
                elif re.match(r"^[a-z][a-z-]*$", rest[0]):
                    failures.append(
                        f'{rel}: `kb {raw}` — "{rest[0]}" is not a {verb} subcommand '
                        f"(have: {' '.join(entry['subcommands'])})")
                    continue
            for tok in rest:
                if not tok.startswith("--"):
                    continue
                flag = re.sub(r"[.,;:)]+$", "", tok.split("=")[0])
                if flag not in flag_set and flag not in global_flags:
                    failures.append(f'{rel}: `kb {raw}` — "{flag}" is not an option of '
                                    f"`kb {verb}`")

    if failures:
        print(f"kb command check: {len(failures)} failure(s)\n", file=sys.stderr)
        for f in dict.fromkeys(failures):
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"kb command check: every documented kb command exists ({len(verbs)} verbs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
