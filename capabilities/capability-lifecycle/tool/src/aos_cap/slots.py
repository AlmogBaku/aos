"""{{skill:}} and {{agent:}} slot resolution — §2.5's computed names, applied to prose.

Installed names are COMPUTED, so shipped prose carries a slot, never a literal:
`{{skill: <id>}}` / `{{agent: <id>}}` for this capability's own, `{{skill: <cap>/<id>}}`
for another capability's. Agents share the capability's `skill_prefix`.

This is the DETERMINISTIC half of replacement. The other half is agentic: a user writing
"use the route skill" in their MOD.md has no slot to match, and the transform resolves that
while weaving. Neither half handles the other's case, by design.

Deliberately NOT the {{mod}} rule: an unresolved {{mod}} slot is left intact by contract
(the agentic transform fills it later), while an unresolvable slot here is a hard failure.
A silent pass-through is what let a prefix rename invalidate 100+ references with green CI.
"""

import re
from pathlib import Path
from typing import Optional

from .names import (
    declared_agent_ids, effective_prefix, installed_name, resolve_capability,
)

# A leading backslash escapes the slot: `\{{skill: <id>}}` renders as a literal
# `{{skill: <id>}}`, unsubstituted AND unvalidated. capability-lifecycle documents the
# syntax it is itself rendered by, so without this, installing it corrupts its own naming
# reference. `mod` is included in the unescape so the rule is ONE sentence an author can
# hold: "a backslash before any {{...}} slot makes it a literal example."
SKILL_SLOT = re.compile(r"(?<!\\)\{\{skill:\s*([a-z0-9-]+)(?:/([a-z0-9-]+))?\s*\}\}")
AGENT_SLOT = re.compile(r"(?<!\\)\{\{agent:\s*([a-z0-9-]+)(?:/([a-z0-9-]+))?\s*\}\}")
ESCAPED_SLOT = re.compile(r"\\(\{\{(?:skill|agent|mod):[^}]*\}\})")


def _declared_skill_ids(manifest: dict, cap_dir: Path) -> set[str]:
    """Declared skill ids — the manifest is the source, since an undeclared on-disk skill
    is a manifest error (`skills: on-disk skill '<id>' is not declared`) and a slot must
    not be resolvable through one."""
    ids = {e.get("id") for e in (manifest.get("skills") or []) if isinstance(e, dict)}
    return {i for i in ids if isinstance(i, str) and i}


def resolve_slots(text: str, cap_dir: Path, manifest: dict,
                  rel: str) -> tuple[str, list[str]]:
    """(rewritten text, errors). `rel` is how the file is named in an error message.

    Order matters: skills, then agents, then the unescape LAST — so an escaped slot was
    never a substitution candidate (the `(?<!\\)` guards saw the backslash) and was never
    validated either. An example naming a placeholder capability is not a dangling
    reference.
    """
    cap_dir = Path(cap_dir).resolve()
    cap_id = cap_dir.name
    own_prefix = effective_prefix(manifest, cap_id)
    errors: list[str] = []
    # Memoized per CALL, keyed by capability id: `resolve()` below is a regex callback, so
    # a file with ten slots naming one foreign capability would otherwise read and parse
    # that capability's manifest ten times. Local, so there is no cache-invalidation
    # question — the dict cannot outlive the one file it was built for.
    seen: dict[str, tuple[Optional[Path], Optional[dict], bool]] = {}

    def foreign(dep_id: str):
        if dep_id not in seen:
            seen[dep_id] = resolve_capability(dep_id, cap_dir)
        return seen[dep_id]

    def resolve(m: "re.Match[str]", kind: str) -> str:
        first, second = m.group(1), m.group(2)
        slot = m.group(0)
        if second is None:                      # own capability
            target_id, target_dir, target_mf = first, cap_dir, manifest
        else:                                   # <cap>/<id>
            target_id = second
            target_dir, target_mf, shadowed = foreign(first)
            if target_dir is None:
                errors.append(
                    f"{rel}: {slot} names capability '{first}', which resolves in neither "
                    f"personal/ nor upstream/")
                return slot
            if shadowed:
                errors.append(
                    f"{rel}: {slot} names capability '{first}', which exists in BOTH "
                    f"personal/ and upstream/ — resolve the shadow rather than let a slot "
                    f"pick one silently")
                return slot
            if target_mf is None:
                errors.append(f"{rel}: {slot}: capability '{first}' has an unreadable "
                              f"CAPABILITY.md")
                return slot
        target_cap = target_dir.name
        prefix = own_prefix if second is None else effective_prefix(target_mf, target_cap)
        if kind == "skill":
            declared = _declared_skill_ids(target_mf, target_dir)
        else:
            declared = declared_agent_ids(target_dir)
        if target_id not in declared:
            errors.append(
                f"{rel}: {slot} names no declared {kind} — {target_cap} declares "
                f"{sorted(declared) or 'none'}")
            return slot
        return installed_name(target_cap, prefix, target_id)

    text = SKILL_SLOT.sub(lambda m: resolve(m, "skill"), text)
    text = AGENT_SLOT.sub(lambda m: resolve(m, "agent"), text)
    text = ESCAPED_SLOT.sub(r"\1", text)
    return text, errors


def resolve_tree(root: Path, cap_dir: Path, manifest: dict) -> list[str]:
    """Resolve every `*.md` under a render in place. Returns the accumulated errors —
    the caller decides what a dangling slot costs (render: exit 18, after removing the
    half-substituted directory)."""
    errors: list[str] = []
    for path in sorted(Path(root).rglob("*.md")):
        if not path.is_file() or path.is_symlink():
            continue
        text = path.read_text()
        out, errs = resolve_slots(text, cap_dir, manifest, str(path.relative_to(root)))
        errors.extend(errs)
        if out != text:
            path.write_text(out)
    return errors


__all__ = ["SKILL_SLOT", "AGENT_SLOT", "ESCAPED_SLOT", "resolve_slots", "resolve_tree"]
