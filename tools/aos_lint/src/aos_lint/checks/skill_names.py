import re

from ..constants import AGENT_SLOT, HISTORICAL_NAME_MARKER, SKILL_SLOT
from ..frontmatter import read_frontmatter
from ..names import (
    capability_agent_name_map, capability_skill_name_map, effective_prefix, installed_name,
    is_prefix_well_formed, name_problems,
)
from ..repo import list_capabilities


# The only cross-capability check in the suite. Skills land in one flat namespace per
# harness, so two capabilities computing the same installed name is a silent override —
# the same hazard §5.5's single-owner rule closes for schedules. Everything here works
# off ctx.caps, never ctx.files: the golden snapshots contain dozens of rendered
# SKILL.md copies that are not shipped skills.
def check_skill_names(ctx) -> None:
    # A personal capability must be unique against the kit too (capability-build's
    # post-build gate lints the personal root with the kit as a dep_root).
    foreign = {}
    for dep_root in ctx.dep_roots:
        for cap in list_capabilities(dep_root):
            for name in capability_skill_name_map(cap):
                foreign[name] = f'capability "{cap.id}" in {dep_root}'

    claimed = {}
    for cap in ctx.caps:
        manifest = read_frontmatter(cap.dir / "CAPABILITY.md").data or {}
        declared = manifest.get("skill_prefix", _MISSING)
        if (declared is not _MISSING and declared is not None
                and not (isinstance(declared, str) and not declared.strip())
                and not is_prefix_well_formed(declared)):
            ctx.report("error", "skills/prefix-format", f"{cap.rel}/CAPABILITY.md",
                       f'skill_prefix "{declared}" must be [a-z0-9-] ending in a hyphen '
                       f'(e.g. "capability-"); omit it to default to "{cap.id}-"')
        prefix = effective_prefix(manifest, cap.id)

        for entry in manifest.get("skills") or []:
            skill_id = entry.get("id") if isinstance(entry, dict) else None
            if not isinstance(skill_id, str) or not skill_id:
                continue  # manifest.py owns shape errors
            name = installed_name(cap.id, prefix, skill_id)
            where = f"{cap.rel}/skills/{skill_id}/SKILL.md"

            # Authors write bare, capability-local ids: the prefix is applied once, by the tool.
            if skill_id != cap.id and skill_id.startswith(prefix):
                ctx.report("error", "skills/prefix-redundant", where,
                           f'id "{skill_id}" already carries the prefix "{prefix}" — ship the '
                           f'bare id ("{skill_id[len(prefix):]}"); the installed name is '
                           f"computed (§2.5)")
            for problem in name_problems(name):
                ctx.report("error", "skills/installed-name", where,
                           f'installed name "{name}" {problem}')
            owner = claimed.get(name) or foreign.get(name)
            if owner:
                ctx.report("error", "skills/installed-collision", where,
                           f'installed name "{name}" is already claimed by {owner} — one flat '
                           f"namespace per harness, so this would silently override")
            else:
                claimed[name] = f"{cap.id}:{skill_id}"

    _check_qualified_refs(ctx)
    _check_authored_names(ctx)


class _Missing:
    """`skill_prefix:` absent and `skill_prefix: null` are different manifests — the first
    defaults to the capability id, the second is an author writing nothing where a prefix
    goes. `.get(k)` collapses them; this sentinel keeps them apart, as the JS `undefined`
    vs `null` test did."""


_MISSING = _Missing()


# The mirror image of _check_qualified_refs, and the defect that motivated both. That one
# catches a BARE sibling id in shipped prose; this one catches the computed installed name
# written LITERALLY — the case that let `skill_prefix: capability-` → `lc-` rename 80+
# references with green CI, because a literal is only wrong relative to a prefix nothing
# re-derived. Deliberately lint's job and not a runtime gate's: a hardcoded name and a
# dangling slot are both mechanically decidable, and CI is where the author is. (Informal
# prose — "hand it to the archiver" — is the non-mechanical half, and belongs to
# capability-review §6a.)
def _check_authored_names(ctx) -> None:
    # Every installed name in the repo, and who owns it — so a literal naming ANOTHER
    # capability's skill gets told the qualified slot (`{{skill: <cap>/<id>}}`) rather than
    # the local one.
    owners = {}     # installed name -> (cap_id, id, kind)
    for cap in ctx.caps:
        for name, skill_id in capability_skill_name_map(cap).items():
            # installed_name() returns the id unchanged when id == cap.id, so an entry-skill
            # name is not prefix-fragile: `kb` stays `kb` under any prefix, and demanding a
            # slot for it would be noise. Only names the prefix actually rewrites can rot.
            if name != skill_id:
                owners[name] = (cap.id, skill_id, "skill")
        for name, agent_id in capability_agent_name_map(cap).items():
            if name != agent_id:
                owners[name] = (cap.id, agent_id, "agent")

    # What a slot may resolve to, per capability: declared skills (the manifest is the source,
    # as in slots.py — an undeclared on-disk skill is its own error and must not make a slot
    # resolvable) and declared agents.
    declared = {}
    for cap in ctx.caps:
        manifest = read_frontmatter(cap.dir / "CAPABILITY.md").data or {}
        declared[cap.id] = {
            "skill": {e.get("id") for e in (manifest.get("skills") or [])
                      if isinstance(e, dict) and isinstance(e.get("id"), str) and e["id"]},
            "agent": set(capability_agent_name_map(cap).values()),
        }

    literal_re = None
    if owners:
        # Longest first, so `kb-import` is not matched as `kb` — the alternation is ordered,
        # and Python's `|` is first-match just as JS's is.
        alts = "|".join(re.escape(n) for n in sorted(owners, key=len, reverse=True))
        literal_re = re.compile(rf"`({alts})`")

    for cap in ctx.caps:
        # RENDERED prose only. CAPABILITY.md is the installer's briefing — read from the clone,
        # never rendered — so it keeps literal names; same for docs/, README.md, BOOTSTRAP.md
        # and AGENTS.md, which describe the kit rather than ship into a harness. cap.rel also
        # keeps the golden snapshots' rendered copies (which correctly hold literals) out.
        scope = f"{cap.rel}/skills/"
        for file in [f for f in ctx.files if f.startswith(scope) and f.endswith(".md")]:
            try:
                text = (ctx.root / file).read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(text.split("\n")):
                where = f"{file}:{i + 1}"
                # Migration prose names retired skills on purpose; the marker keeps that
                # intent on the line rather than in a path allowlist that would rot.
                if HISTORICAL_NAME_MARKER in line:
                    continue

                if literal_re:
                    for hit in dict.fromkeys(m.group(1) for m in literal_re.finditer(line)):
                        owner_cap, owner_id, kind = owners[hit]
                        slot = (f"{{{{{kind}: {owner_id}}}}}" if owner_cap == cap.id
                                else f"{{{{{kind}: {owner_cap}/{owner_id}}}}}")
                        ctx.report("error", "skills/ref-hardcoded", where,
                                   f'"`{hit}`" is a computed installed name written as a '
                                   f"literal — use {slot} so a {owner_cap} prefix change "
                                   f"cannot invalidate it (§2.5)")

                # The escaped form (`\{{skill: <id>}}`) is invisible here for the same reason
                # it is invisible to render: the shared regexes carry the `(?<!\\)` guard. A
                # doc that teaches the syntax must not be a lint failure.
                for pattern, kind, code in [
                    (SKILL_SLOT, "skill", "skills/ref-dangling"),
                    (AGENT_SLOT, "agent", "agents/ref-dangling"),
                ]:
                    for m in pattern.finditer(line):
                        first, second = m.group(1), m.group(2)
                        target_cap = cap.id if second is None else first
                        target_id = first if second is None else second
                        known = declared.get(target_cap)
                        if known is None:
                            ctx.report("error", code, where,
                                       f'{m.group(0)} names capability "{target_cap}", which '
                                       f"is not in this tree")
                        elif target_id not in known[kind]:
                            ctx.report("error", code, where,
                                       f"{m.group(0)} names no {kind} declared by "
                                       f'"{target_cap}" — it declares '
                                       f"{', '.join(sorted(known[kind])) or 'none'}")


# Cross-skill references resolve by name at runtime (crosspath.py bans relative paths),
# and the name a harness knows is the installed one. A bare sibling id in shipped prose
# points at nothing once installed. Scoped to "`<id>` skill" / "the `<id>` skill" so it
# never fires on a tool verb — `kb capture`, `kb import survey`, `aos-cap init`.
def _check_qualified_refs(ctx) -> None:
    for cap in ctx.caps:
        bare = {}
        for name, skill_id in capability_skill_name_map(cap).items():
            if name != skill_id:
                bare[skill_id] = name       # only ids the prefix actually rewrites
        if not bare:
            continue
        ids = "|".join(re.escape(i) for i in bare)
        patterns = [
            # "the `capture` skill" — prose. The adjacent "skill" is what keeps this off tool
            # verbs (`kb capture`, `kb import survey`, `aos-cap init`).
            re.compile(rf"`({ids})`\s+skill\b"),
            # A routing-table cell that is nothing but the id — the mechanics map in every
            # entry skill. Tool verbs in a cell carry their command (`kb capture`), so they
            # don't match.
            # No re.M: the scan is per LINE, so `$` already means end of line, and re.M would
            # additionally match before a trailing newline a split line cannot have.
            re.compile(rf"\|\s*`({ids})`\s*(?=\||$)"),
        ]

        # cap.rel scopes this to the capability's own tree, so the golden snapshots' rendered
        # copies are never read.
        for file in [f for f in ctx.files
                     if f.startswith(f"{cap.rel}/") and f.endswith(".md")]:
            try:
                text = (ctx.root / file).read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(text.split("\n")):
                hits = []
                for pattern in patterns:
                    for m in pattern.finditer(line):
                        if m.group(1) not in hits:
                            hits.append(m.group(1))
                for hit in hits:
                    ctx.report("error", "skills/ref-unqualified", f"{file}:{i + 1}",
                               f'"`{hit}`" names a capability-local skill id — installed it '
                               f'is "{bare[hit]}" (§2.5)')
