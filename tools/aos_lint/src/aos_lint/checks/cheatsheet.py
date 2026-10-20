import re

from ..constants import (
    CHEATSHEET_CONCEPTS, CHEATSHEET_KEYS, CHEATSHEET_ROWS, CHEATSHEET_SECTIONS,
    CHEATSHEET_STATUS, CHEATSHEET_SUPPORT, SESSION_KEYS,
)
from ..frontmatter import read_frontmatter

_IN_REFERENCE = re.compile(r"/reference/harness-[^/]+\.md$")
_LEGACY = re.compile(r"^(?:capabilities/[^/]+/)?harnesses/(?!README\.md$)[^/]+\.md$")
_H2 = re.compile(r"^##\s+(.+?)\s*$", re.M)


# ARCHITECTURE §5.2 — a cheat-sheet is content for the installer plus a schema-checked
# frontmatter: the six sections must exist as H2 headings, and the frontmatter must answer
# the same questions on every harness. A cheat-sheet is a reference file of the skill that
# consumes it — `skills/<entry>/reference/harness-<harness-runtime>.md` — so it travels with the
# render and resolves from an installed skill. The old capability-level `harnesses/<runtime>.md`
# shape did neither: nothing beside an installed skill has a `harnesses/` sibling, so a skill
# telling the agent to load one sent it hunting.
def check_cheatsheets(ctx) -> None:
    for rel in ctx.files:
        if not _IN_REFERENCE.search(rel) and not _LEGACY.match(rel):
            continue
        text = (ctx.root / rel).read_text(encoding="utf-8")
        headings = [m.group(1).lower() for m in _H2.finditer(text)]
        for section in CHEATSHEET_SECTIONS:
            if section.lower() not in headings:
                ctx.report("error", "cheatsheet/section", rel,
                           f'missing required section "## {section}" (ARCHITECTURE §5.2)')
        for message in _frontmatter_errors(ctx.root / rel):
            ctx.report("error", "cheatsheet/key", rel, message)


# One code, many messages: every way a sheet's frontmatter can fail to answer the questions
# every harness must answer. The frontmatter is what programs read (`aos-session` reads
# `mapping.session`; the install step reads the host-word rows), so a gap here is a gap a
# program meets at run time, not a style nit.
def _frontmatter_errors(path) -> list[str]:
    parsed = read_frontmatter(path)
    if parsed.error:
        return [f"frontmatter does not parse: {parsed.error}"]
    fm = parsed.data
    if fm is None:
        return ["no frontmatter — a cheat-sheet opens with the §5.2 frontmatter "
                "(harness, status, source, rules, files, mapping)"]
    errs = []
    for key in sorted(CHEATSHEET_KEYS - set(fm)):
        errs.append(f"missing key `{key}`")
    for key in sorted(set(fm) - CHEATSHEET_KEYS):
        errs.append(f"unknown key `{key}` — a fact of one harness goes in a row's notes or the body")
    if "status" in fm and fm["status"] not in CHEATSHEET_STATUS:
        errs.append(f"status `{fm['status']}` must be one of {sorted(CHEATSHEET_STATUS)}")
    for key in ("source", "harness"):
        if key in fm and (not isinstance(fm[key], str) or not fm[key].strip()):
            errs.append(f"`{key}` must be a non-empty string")
    for key in ("rules", "files"):
        if key in fm and not isinstance(fm[key], list):
            errs.append(f"`{key}` must be a list")
    mapping = fm.get("mapping")
    if "mapping" in fm and not isinstance(mapping, dict):
        return errs + ["`mapping` must be a mapping of rows"]
    mapping = mapping or {}
    for row in CHEATSHEET_ROWS:
        if row not in mapping:
            errs.append(f"mapping.{row} is missing (every sheet answers every row)")
    for row in mapping:
        if row not in CHEATSHEET_ROWS:
            errs.append(f"mapping.{row} is not a row — the rows are the ten concepts and the "
                        f"depends.host words")
    for row, value in mapping.items():
        if row in CHEATSHEET_ROWS:
            errs.extend(_row_errors(row, value))
    return errs


def _row_errors(row: str, value) -> list[str]:
    where = f"mapping.{row}"
    if not isinstance(value, dict):
        return [f"{where} must be a mapping with `primitive` or `support`"]
    has_primitive = "primitive" in value
    support = value.get("support")
    if has_primitive == ("support" in value):
        return [f"{where}: exactly one of `primitive` (the harness has it) or `support`"]
    errs = []
    if not has_primitive:
        if support not in CHEATSHEET_SUPPORT:
            errs.append(f"{where}: support `{support}` must be one of {sorted(CHEATSHEET_SUPPORT)}")
        if support == "via" and not value.get("via"):
            errs.append(f"{where}: support via names what to install, in `via:`")
        if support == "none" and row in CHEATSHEET_CONCEPTS and not value.get("instead"):
            errs.append(f"{where}: support none on a concept says what the installer does "
                        f"`instead:`")
    elif row == "session":
        for key in SESSION_KEYS:
            if key not in value:
                errs.append(f"{where}: `{key}` is missing — aos-session reads it at run time")
    return errs
