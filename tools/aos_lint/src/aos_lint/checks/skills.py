import re

from ..constants import (
    LEGACY_ORIGIN_FRONTMATTER_KEY, MAIN_AGENT, ORIGIN_FRONTMATTER_KEY,
    ORIGIN_FRONTMATTER_PATH, REFERENCE_TOC_LINES, RESERVED_NAME_WORDS, SKILL_NAME_MAX,
    SKILL_NAME_RE,
)
from ..frontmatter import read_frontmatter
from .agents import agent_names

# Agent Skills spec (agentskills.io/specification) — the portable core every
# skills/<id>/ folder must satisfy standalone (ARCHITECTURE §2.1 normative).
SKILL_KEYS = ["name", "description", "license", "allowed-tools", "metadata", "compatibility"]
NAME_RE = SKILL_NAME_RE
# The spec forbids XML tags in name/description: both are injected into the system prompt,
# where an angle-bracket token reads as markup. Placeholders belong in the body.
XML_TAG_RE = re.compile(r"<[^\s>]+>")

_POV_RE = re.compile(
    r"\b(?:I can|I will|I help|I'll|helps? you|lets you|allows you|enables you|you can|"
    r"you should|use this (?:to|when|for))\b", re.I)

_SENTINEL = object()


def check_skills(ctx) -> None:
    for cap in ctx.caps:
        manifest = read_frontmatter(cap.dir / "CAPABILITY.md").data or {}
        declared = {e.get("id"): e for e in (manifest.get("skills") or [])
                    if isinstance(e, dict)}
        agents = agent_names(cap)

        # Every SKILL.md in the capability must be a valid Agent Skills folder —
        # including methodology-shipped ones outside skills/ (those aren't in the
        # manifest bijection; the methodology contract carries them).
        skill_files = [f for f in ctx.files
                       if f.startswith(f"{cap.rel}/") and f.endswith("/SKILL.md")]
        for file in skill_files:
            parts = file.split("/")
            skill_id = parts[-2]
            in_skills_dir = parts[2] == "skills" and len(parts) == 5
            path = cap.dir.joinpath(*parts[2:])
            parsed = read_frontmatter(path)
            if parsed.error or parsed.data is None:
                ctx.report("error", "skill/parse", file,
                           parsed.error or "missing frontmatter")
                continue
            data, body = parsed.data, parsed.body

            # Strict-portable profile: shipped skills carry only spec fields. Harness-
            # specific extension goes in metadata.<harness>.* per the spec's own escape hatch.
            for key in data:
                if key == LEGACY_ORIGIN_FRONTMATTER_KEY:
                    ctx.report("error", "skill/origin-tag", file,
                               f"{LEGACY_ORIGIN_FRONTMATTER_KEY} is retired — the stamp is "
                               f"{ORIGIN_FRONTMATTER_KEY}, and it is an install-time tag never "
                               f"shipped upstream")
                elif key not in SKILL_KEYS:
                    ctx.report("error", "skill/unknown-key", file,
                               f'"{key}" is not an Agent Skills spec field (allowed: '
                               f"{', '.join(SKILL_KEYS)})")
            # The stamp moved inside `metadata`, so rejecting the old top-level key is no
            # longer enough — an upstream skill carrying metadata.aos.origin is the same
            # defect wearing the new spelling, and a check that only knew the old one would
            # pass it silently.
            if _read_origin(data) is not _SENTINEL:
                ctx.report("error", "skill/origin-tag", file,
                           f"{ORIGIN_FRONTMATTER_KEY} is an install-time tag — never shipped "
                           f"upstream")
            name = data.get("name")
            if (not isinstance(name, str) or not name or len(name) > SKILL_NAME_MAX
                    or not NAME_RE.match(name)):
                ctx.report("error", "skill/name", file,
                           f"name must be 1–{SKILL_NAME_MAX} chars of [a-z0-9-], no "
                           f"leading/trailing/double hyphens")
            elif name != skill_id:
                ctx.report("error", "skill/name-dir", file,
                           f'name "{name}" must equal directory name "{skill_id}"')
            if isinstance(name, str):
                for word in RESERVED_NAME_WORDS:
                    if word in name:
                        ctx.report("error", "skill/reserved-word", file,
                                   f'name "{name}" contains the reserved word "{word}" '
                                   f"(Agent Skills spec)")
            desc = data.get("description")
            if not isinstance(desc, str) or not desc.strip() or len(desc) > 1024:
                ctx.report("error", "skill/description", file,
                           "description is required, 1–1024 chars")
            elif not re.search(r"\bwhen\b", desc, re.I):
                ctx.report("warn", "skill/description-when", file,
                           "description should say when to use the skill (trigger phrasing)")
            # A description is injected into the system prompt to choose among a hundred
            # skills, so its point of view is load-bearing: the authoring guide calls
            # first/second person a discovery problem, not a style preference. Every shipped
            # skill already passes, which is why this is an error rather than a warning — it
            # guards a property we have, instead of reporting one we lack. The review skill's
            # reference/skill-rubric.md carries the judgment half of description quality,
            # which no regex can reach.
            if isinstance(desc, str):
                pov = _POV_RE.search(desc)
                if pov:
                    ctx.report("error", "skill/description-person", file,
                               f'description says "{pov.group(0)}" — write it in third person '
                               f'("Records a thought…", not "I can help you…" or "Use this '
                               f'to…"); it is injected into the system prompt')
            for field, value in (("name", name), ("description", desc)):
                if isinstance(value, str) and XML_TAG_RE.search(value):
                    ctx.report("error", "skill/xml-tags", file,
                               f'{field} contains "{XML_TAG_RE.search(value).group(0)}" — no '
                               f"XML tags in frontmatter (it is injected into the system "
                               f"prompt); use a plain placeholder or move the example into "
                               f"the body")
            if len(body.split("\n")) > 500:
                ctx.report("warn", "skill/body-length", file,
                           "SKILL.md body exceeds 500 lines — split into sections/ "
                           "(progressive disclosure)")

            # used_by scoping (ARCHITECTURE §2.2, normative — the anti-pollution rule).
            # Only skills/<id>/ entries participate in the manifest bijection.
            entry = declared.get(skill_id) if in_skills_dir else None
            if entry:
                used_by = entry.get("used_by")
                if not isinstance(used_by, list) or not used_by:
                    ctx.report("error", "skill/used-by", f"{cap.rel}/CAPABILITY.md",
                               f'skill "{skill_id}" must declare a non-empty used_by list')
                else:
                    for u in used_by:
                        if u != MAIN_AGENT and u not in agents:
                            ctx.report("error", "skill/used-by-ref",
                                       f"{cap.rel}/CAPABILITY.md",
                                       f'skill "{skill_id}" used_by "{u}" is neither '
                                       f'"{MAIN_AGENT}" nor a declared agent')

        _check_reference_depth(ctx, cap)

        # §2.2: a multi-skill capability scoping everything to main is the degenerate case the
        # linter questions — but only where an alternative EXISTED. A capability with no agents
        # and no schedules has no role to scope to, so "is that deliberate?" is unanswerable
        # rather than unanswered, and a warning nobody can act on is one people learn to ignore.
        # (capability-lifecycle is the case: install/upgrade/remove are all things the user asks
        # the front agent.) A capability that LATER declares an agent and forgets to scope a
        # skill to it fires this again, which is the signal worth keeping.
        has_roles = bool(agents) or bool(manifest.get("schedules") or [])
        all_used_by = [u for e in declared.values() for u in (e.get("used_by") or [])]
        if (has_roles and len(declared) > 1 and all_used_by
                and all(u == MAIN_AGENT for u in all_used_by)):
            ctx.report("warn", "skill/all-main", f"{cap.rel}/CAPABILITY.md",
                       "every skill is scoped to main — is that deliberate? (§2.2)")


# The stamp, read as structured data at whatever depth the spec hatch puts it.
def _read_origin(data):
    node = data
    for key in ORIGIN_FRONTMATTER_PATH:
        if not isinstance(node, dict) or key not in node:
            return _SENTINEL
        node = node[key]
    return node


# Two forms, because authors write both and the truncation is identical: a markdown link
# `](deep.md)`, and a backticked path `` `reference/deep.md` `` — which is in fact the
# commoner shape in this kit. Matching only the link form left the majority invisible.
# The basename is compared, so `reference/x.md` and `./x.md` and `x.md` all resolve to the
# same sibling; a file naming ITSELF is not a violation, and neither is a path into a
# different skill's reference/ (that is skill/no-cross-path's job).
#
# Only a path that RESOLVES to a sibling counts. Matching on basename alone made a
# legitimate cross-skill reference by installed name (`kb-route/reference/lifecycle.md`)
# fire against this skill's own `lifecycle.md` — the case the comment above claims is
# safe. So a bare `x.md`, `./x.md` or `reference/x.md` is a sibling reference; anything
# carrying a longer prefix is somebody else's file and is `skill/no-cross-path`'s to judge.
NESTED_RE = re.compile(
    r"]\((?:\./)?([A-Za-z0-9._/-]+\.md)(?:[#\"'][^)]*)?\)"
    r"|`(?:\./)?([A-Za-z0-9._/-]+\.md)(?:#[A-Za-z0-9._-]+)?`")

_CONTENTS_RE = re.compile(r"^#{1,3}\s*contents\b", re.I)


# Progressive disclosure, per the Agent Skills authoring guide: every reference file hangs
# directly off SKILL.md. A file reached *through* another one gets partially read (the
# agent previews with head -100 rather than reading it whole), so a chain silently
# truncates. And past ~100 lines a preview no longer shows the file's scope — hence the
# Contents block.
def _check_reference_depth(ctx, cap) -> None:
    refs = [f for f in ctx.files if f.startswith(f"{cap.rel}/") and f.endswith(".md")
            and "reference" in f.split("/")]
    for file in refs:
        directory = file.rsplit("/", 1)[0]
        siblings = {f[len(directory) + 1:] for f in refs if f.startswith(f"{directory}/")}
        try:
            text = cap.dir.joinpath(*file.split("/")[2:]).read_text(encoding="utf-8")
        except OSError:
            continue
        self_name = file[len(directory) + 1:]
        for m in NESTED_RE.finditer(text):
            ref = m.group(1) if m.group(1) is not None else m.group(2)
            parts = ref.split("/")
            # sibling-shaped: `x.md` or `reference/x.md`, nothing deeper
            if len(parts) > 2 or (len(parts) == 2 and parts[0] != "reference"):
                continue
            target = parts[-1]
            if target != self_name and target in siblings:
                ctx.report("error", "skill/nested-reference", file,
                           f'references the sibling "{target}" — every reference file must '
                           f"hang directly off SKILL.md, or it gets read only in part (name "
                           f"the SKILL instead, and let it link both)")
        lines = text.split("\n")
        if (len(lines) > REFERENCE_TOC_LINES
                and not any(_CONTENTS_RE.match(line) for line in lines[:15])):
            ctx.report("warn", "skill/reference-toc", file,
                       f'{len(lines)} lines with no "## Contents" block — a partial read must '
                       f"still show the file's scope")
