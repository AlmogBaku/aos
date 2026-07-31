import re

from ..constants import CHEATSHEET_SECTIONS

_IN_REFERENCE = re.compile(r"/reference/harness-[^/]+\.md$")
_LEGACY = re.compile(r"^(?:capabilities/[^/]+/)?harnesses/(?!README\.md$)[^/]+\.md$")
_H2 = re.compile(r"^##\s+(.+?)\s*$", re.M)


# ARCHITECTURE §5.2 — a cheat-sheet is a contract of content, not API: the six
# sections must exist as H2 headings. A cheat-sheet is a reference file of the skill
# that consumes it — `skills/<entry>/reference/harness-<harness-runtime>.md` — so it
# travels with the render and resolves from an installed skill. The old capability-level
# `harnesses/<runtime>.md` shape did neither: nothing beside an installed skill has a
# `harnesses/` sibling, so a skill telling the agent to load one sent it hunting.
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
