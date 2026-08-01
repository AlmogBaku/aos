"""Installed-name computation — IMPORTED from the shipped tool, not reimplemented.

This is the file the port existed to delete. `tools/lib/skill-names.mjs` computed installed
names in JS, carried the comment "Mirrored in aos_cap/names.py … the two must agree; the
goldens are the tie-break", and nothing tested the agreement. The mirror had grown from four
shared concepts to nine. So rather than test a duplication: `effective_prefix`,
`installed_name`, `name_errors`, `capability_skill_names`, `capability_agent_names` and
`declared_agent_ids` are the SHIPPED tool's functions, and the lint calls them.

Two shape differences between "what the installer needs" and "what the linter needs" remain
on this side:

  - the shipped `capability_skill_names` returns a SET of installed names; lint needs the id
    each name came from, to tell an author which bare id to write. So the map below gathers
    ids and applies the imported `installed_name` to each — and then asserts its own keys
    equal the shipped function's set, which is the agreement the .mjs mirror only promised.
  - `is_prefix_well_formed` has no runtime caller: the tool takes the prefix as given, and
    rejecting a malformed one is the lint's job. So it lives here.
"""

from pathlib import Path

from aos_cap.names import (  # noqa: F401  (re-exported: one implementation, not a mirror)
    capability_agent_names,
    capability_skill_names,
    declared_agent_ids,
    effective_prefix,
    installed_name,
    name_errors,
)

from .constants import SKILL_PREFIX_RE
from .frontmatter import read_frontmatter


def is_prefix_well_formed(prefix) -> bool:
    return isinstance(prefix, str) and bool(SKILL_PREFIX_RE.match(prefix))


def name_problems(name: str) -> list[str]:
    """The Agent Skills limits as the lint phrases them. `aos_cap.name_errors` is the single
    implementation of WHICH limits apply; this only restates them in the linter's message
    shape (the tool's messages stand alone, so they repeat the name; a lint finding already
    carries the file and the name)."""
    return [err[len(f"name '{name}' "):] for err in name_errors(name, "name")]


def _manifest(cap) -> dict:
    return read_frontmatter(Path(cap.dir) / "CAPABILITY.md").data or {}


def capability_skill_name_map(cap) -> dict[str, str]:
    """installed name -> the capability-local id it came from.

    The id set is the shipped function's: declared manifest entries plus any on-disk skill
    dir (an undeclared dir is its own error, but it would still land if installed). Only the
    id->name PAIRING is added here, and the assert keeps that honest — inverting the prefix
    instead would have mis-attributed a prefix-redundant id (`kb-foo` inverts to `foo`, and
    then `skills/ref-hardcoded` would demand a slot for a name that is not prefix-fragile).
    """
    prefix = effective_prefix(_manifest(cap), cap.id)
    ids = {e.get("id") for e in (_manifest(cap).get("skills") or []) if isinstance(e, dict)}
    skills_dir = Path(cap.dir) / "skills"
    if skills_dir.is_dir():
        ids |= {d.name for d in skills_dir.iterdir() if (d / "SKILL.md").is_file()}
    out = {installed_name(cap.id, prefix, i): i
           for i in sorted(i for i in ids if isinstance(i, str) and i)}
    _agree(out, capability_skill_names(Path(cap.dir)), cap, "skill")
    return out


def capability_agent_name_map(cap) -> dict[str, str]:
    """The agent twin — installed name -> declared agent name."""
    prefix = effective_prefix(_manifest(cap), cap.id)
    out = {installed_name(cap.id, prefix, a): a
           for a in sorted(declared_agent_ids(Path(cap.dir)))}
    _agree(out, capability_agent_names(Path(cap.dir)), cap, "agent")
    return out


def _agree(mapped: dict, shipped: set, cap, what: str) -> None:
    """The agreement the deleted JS mirror only claimed. A divergence here means the pairing
    loop above and the shipped tool disagree about what a capability installs — which is
    exactly the class of defect a prefix rename used to slip through with green CI — so it
    raises rather than reporting a finding: the linter's own name computation being wrong
    makes every name finding it emits untrustworthy."""
    if set(mapped) != shipped:
        raise AssertionError(
            f"aos_lint.names: {what} names for '{cap.id}' disagree with aos_cap — "
            f"{set(mapped) ^ shipped}")
