import re

_SKILL_MD = re.compile(r"^capabilities/[^/]+/skills/[^/]+/.*\.md$")
_ENTRY = re.compile(r"^capabilities/[^/]+/skills/[^/]+/SKILL\.md$")

# A bare relative path (no scheme, no anchor, not rooted at a household dir) whose first
# segment is a capability-package directory. Deliberately narrow: `.kb/pending/…` and
# `_raw/…` are paths inside a user's KB, and `<id>-draft/agents/…` is a draft the skill
# writes — neither is a load target in the source tree.
PACKAGE_PATH = re.compile(
    r"(?:\]\(|`)((?:harnesses|adapters|tool|capabilities)/[A-Za-z0-9_<>./-]*\.(?:md|ya?ml))")

_OWN_REF = re.compile(r"(?:\]\(|`)(reference/[A-Za-z0-9_-]+\.md)")
_SKILL_WORD = re.compile(r"\bskill\b", re.I)


# ARCHITECTURE §2.1/§2.5 — in-capability cross-skill references are by skill NAME,
# never by relative path: materialization renames each skill dir to its installed name,
# so an authored ../<dir>/ path breaks at runtime. Relative paths must stay inside
# the skill's own folder (the whole-folder render keeps those intact; link names
# differ from shipped dir names, so cross-skill refs go by name).
def check_cross_paths(ctx) -> None:
    _check_own_references(ctx)
    for rel in ctx.files:
        if not _SKILL_MD.match(rel):
            continue
        text = (ctx.root / rel).read_text(encoding="utf-8")
        if "../" in text:
            ctx.report("error", "skill/no-cross-path", rel,
                       'contains a "../" reference — cross-skill references are by skill name '
                       "(materialized dirs carry the installed name, not the source id, §2.5); "
                       "relative paths must stay inside the skill's own folder")

        # The same failure without a "../": a path into the capability *package*. Only the
        # skill's own folder travels, so `harnesses/hermes.md` or `tool/README.md` resolves
        # in the source tree and nowhere else — the agent goes hunting, which is exactly
        # what a shipped skill must never make it do. Package-level knowledge belongs in a
        # reference/ file of the skill that reads it; package-level *paths* are written from
        # a household root (`<home>/upstream/…`), which does resolve at runtime.
        for m in PACKAGE_PATH.finditer(text):
            ctx.report("error", "skill/package-path", rel,
                       f'references "{m.group(1)}" — that path exists only in the source '
                       f"package, not beside an installed skill. Put the content in this "
                       f"skill's reference/, name the skill that owns it, or write the path "
                       f"from a household root (<home>/upstream/…)")


# The same failure from the other side: a bare `reference/<file>` that lives in a
# DIFFERENT skill's reference dir. It reads as this skill's own depth, resolves to
# nothing, and the agent goes looking. Naming the owning skill is the fix — the agent
# loads that skill, and the path resolves inside it.
def _check_own_references(ctx) -> None:
    skill_dirs = {f.rsplit("/", 1)[0] for f in ctx.files if _ENTRY.match(f)}
    have = {f for f in ctx.files if "/reference/" in f}
    for rel in ctx.files:
        if not _SKILL_MD.match(rel):
            continue
        parts = rel.split("/")
        skill_dir = "/".join(parts[:4])
        if skill_dir not in skill_dirs:
            continue
        # Skill names in this capability — a reference attributed to one of them is fine:
        # the agent loads that skill, and the path resolves inside it.
        cap_prefix = "/".join(parts[:3])
        siblings = [d.split("/")[-1] for d in skill_dirs if d.startswith(cap_prefix)]
        lines = (ctx.root / rel).read_text(encoding="utf-8").split("\n")
        seen = set()
        for i, line in enumerate(lines):
            # The enclosing prose, not just this line: a numbered step wraps over several
            # lines, and attribution at its head still tells the agent where to look.
            context = "\n".join(lines[max(0, i - 3):i + 1])
            attributed = (bool(_SKILL_WORD.search(context))
                          or any(f"`{s}`" in context for s in siblings))
            for m in _OWN_REF.finditer(line):
                ref = m.group(1)
                if f"{skill_dir}/{ref}" in have or attributed or ref in seen:
                    continue
                seen.add(ref)
                ctx.report("error", "skill/foreign-reference", f"{rel}:{i + 1}",
                           f'names "{ref}", which is not in this skill\'s own reference/ and '
                           f'is not attributed — say which skill owns it ("the `<skill>` '
                           f"skill's `{ref}`\"), so the agent loads that skill and the path "
                           f"resolves inside it")
