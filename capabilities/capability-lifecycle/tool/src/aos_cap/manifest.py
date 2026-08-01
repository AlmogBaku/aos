"""CAPABILITY.md validation (§2.2) — the one place that decides whether a package is
well-formed. Every check appends to one `errs` list and the whole list is printed
before exit 12, because an installer fixing a manifest wants every problem at once,
not the first one. `skill_rows()` is the shape both `skills` and `render` need, and
`agent_rows()` is its twin for the `agents` verb."""

import sys
from pathlib import Path

from .constants import (
    CAPABILITY_TAGS, CRON5, DEGRADED, HOST_FEATURES, HOST_LEVELS, KB_KEYS,
    MANIFEST_KEYS, SCHEDULE_KEYS, SEMVER, SKILL_ENTRY_KEYS, SKILL_NAME_RE,
    SKILL_PREFIX_RE,
)
from .errors import Exit, fail
from .frontmatter import frontmatter
from .names import (
    declared_agent_ids, effective_prefix, installed_name, name_errors, resolve_capability,
)


def validated_manifest(cap_dir: Path) -> dict:
    # resolve() so a relative invocation (`aos-cap skills .`) still has a directory name
    # to compare `id` against — the contract's commands are written with <cap-dir> paths.
    cap_dir = Path(cap_dir).resolve()
    mf = cap_dir / "CAPABILITY.md"
    if not mf.is_file():
        fail(Exit.MANIFEST_INVALID, f"{cap_dir}: no CAPABILITY.md")
    data = frontmatter(mf)
    errs: list[str] = []
    for key in data:
        if key not in MANIFEST_KEYS and not str(key).startswith("x-"):
            errs.append(f"unknown key '{key}' (rule of two; x-* is the extension namespace)")
    if data.get("id") != cap_dir.name:
        errs.append(f"id '{data.get('id')}' must equal the directory name '{cap_dir.name}'")
    if not isinstance(data.get("version"), str) or not SEMVER.match(data.get("version", "")):
        errs.append(f"version '{data.get('version')}' must be MAJOR.MINOR.PATCH")
    tags = data.get("tags")
    if not isinstance(tags, list) or not tags or not set(tags) <= CAPABILITY_TAGS:
        errs.append(f"tags {tags!r} must be a non-empty subset of {sorted(CAPABILITY_TAGS)}")
    if not isinstance(data.get("summary"), str) or not data.get("summary", "").strip():
        errs.append("summary must be a non-empty string")

    depends = data.get("depends") or {}
    if not isinstance(depends, dict):
        errs.append("depends must be a mapping")
        depends = {}
    for key in depends:
        if key not in ("capabilities", "host"):
            errs.append(f"depends: unknown key '{key}'")
    host = depends.get("host") or {}
    if not isinstance(host, dict):
        errs.append("depends.host must be a mapping")
        host = {}
    for feat, level in host.items():
        if feat not in HOST_FEATURES:
            errs.append(f"depends.host: unknown feature '{feat}'")
        if level not in HOST_LEVELS:
            errs.append(f"depends.host.{feat}: level '{level}' not in {sorted(HOST_LEVELS)}")

    # `main` is the harness's shared agent, which every capability may name; the rest are
    # this package's own. One scan, in names.py, serves both this check and slot resolution
    # — two readers of `agents/*.agent.yaml` could disagree about what an agent is called.
    agent_names = {"main"} | declared_agent_ids(cap_dir)
    # Two-root resolution (the install contract): personal/ first, then upstream/. The
    # old sibling-only lookup failed a CORRECT declaration for every capability
    # `capability-build` writes — those live in personal/ and depend on kb in upstream/.
    for dep in (depends.get("capabilities") or []):
        dep_dir, _, shadowed = resolve_capability(str(dep), cap_dir)
        if dep_dir is None:
            errs.append(f"depends.capabilities: '{dep}' has no capabilities/{dep}/CAPABILITY.md "
                        f"in personal/ or upstream/")
        elif shadowed:
            errs.append(f"depends.capabilities: '{dep}' exists in BOTH personal/ and upstream/ "
                        f"— resolve the shadow before installing (never silently preferred)")
    if not (cap_dir / "README.md").is_file():
        errs.append("README.md is required")
    if (cap_dir / "ONBOARDING.md").is_file() and not (cap_dir / "MOD.example.md").is_file():
        errs.append("ONBOARDING.md without MOD.example.md (presence-paired)")
    seen_sched = set()
    for s in data.get("schedules") or []:
        if not isinstance(s, dict):
            errs.append(f"schedules: entry {s!r} must be a mapping")
            continue
        for key in s:
            if key not in SCHEDULE_KEYS:
                errs.append(f"schedules[{s.get('id')}]: unknown key '{key}'")
        sid = s.get("id")
        if sid in seen_sched:
            errs.append(f"schedules: duplicate id '{sid}'")
        seen_sched.add(sid)
        if not CRON5.match(str(s.get("cron", ""))):
            errs.append(f"schedules[{sid}]: cron '{s.get('cron')}' is not 5-field")
        if sid is None:
            errs.append("schedules: every entry requires an id")
        has_exec = "exec" in s
        has_agent = "agent" in s or "prompt_ref" in s
        if has_exec == has_agent:
            errs.append(f"schedules[{sid}]: exactly one of exec | agent+prompt_ref")
        if has_agent:
            if s.get("agent") not in agent_names:
                errs.append(f"schedules[{sid}]: agent '{s.get('agent')}' is not main or a declared agent")
            pref = s.get("prompt_ref")
            if not pref:
                errs.append(f"schedules[{sid}]: agent form requires prompt_ref")
            elif not (cap_dir / str(pref)).is_file():
                errs.append(f"schedules[{sid}]: prompt_ref '{pref}' does not resolve in the capability")
        if has_exec:
            first = str(s.get("exec", "")).split()[0] if str(s.get("exec", "")).strip() else ""
            if "/" in first and not (cap_dir / first).is_file():
                errs.append(f"schedules[{sid}]: exec path '{first}' does not resolve in the capability")
        if s.get("degraded") is None:
            errs.append(f"schedules[{sid}]: degraded is required (manual|skip|inline)")
        elif s["degraded"] not in DEGRADED:
            errs.append(f"schedules[{sid}]: degraded '{s['degraded']}' not in {sorted(DEGRADED)}")

    # Absent or empty means "default to the capability id" (§2.2), so only a non-empty
    # value is held to the format.
    prefix_declared = data.get("skill_prefix")
    if isinstance(prefix_declared, str) and prefix_declared.strip():
        if not SKILL_PREFIX_RE.match(prefix_declared):
            errs.append(f"skill_prefix '{prefix_declared}' must be [a-z0-9-] ending in a hyphen "
                        f"(e.g. 'capability-'); omit it to default to '<id>-'")
    elif prefix_declared is not None and not isinstance(prefix_declared, str):
        errs.append(f"skill_prefix must be a string (got {prefix_declared!r})")
    prefix = effective_prefix(data, cap_dir.name)

    # Agents ship under a computed name too (`<prefix><agent-id>`, the same prefix), into a
    # flat per-harness namespace — so the same Agent Skills limits are as fatal there as for
    # a skill. Nothing checked this: an `archiver` under a long prefix, or a `claude-router`
    # agent, validated clean and then landed as a name the harness cannot carry.
    for agent_id in sorted(declared_agent_ids(cap_dir)):
        for e in name_errors(installed_name(cap_dir.name, prefix, agent_id),
                             f"agents[{agent_id}]: installed name"):
            errs.append(e)

    declared = set()
    for entry in data.get("skills") or []:
        if not isinstance(entry, dict):
            errs.append(f"skills: entry {entry!r} must be a mapping")
            continue
        for key in entry:
            if key not in SKILL_ENTRY_KEYS:
                errs.append(f"skills[{entry.get('id')}]: unknown key '{key}'")
        sid = entry.get("id")
        declared.add(sid)
        if not (cap_dir / "skills" / str(sid) / "SKILL.md").is_file():
            errs.append(f"skills: declared '{sid}' has no skills/{sid}/SKILL.md")
        if isinstance(sid, str) and SKILL_NAME_RE.match(sid):
            # The installed name is the shipped identity — it carries the spec's limits.
            for e in name_errors(installed_name(cap_dir.name, prefix, sid), f"skills[{sid}]: installed name"):
                errs.append(e)
        else:
            errs.append(f"skills[{sid!r}]: id must be [a-z0-9-], no leading/trailing/double hyphens")
        used = entry.get("used_by")
        if not isinstance(used, list) or not used:
            errs.append(f"skills[{sid}]: used_by must be a non-empty list")
        else:
            for u in used:
                if u not in agent_names:
                    errs.append(f"skills[{sid}]: used_by '{u}' is not main or a declared agent")
    skills_dir = cap_dir / "skills"
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and (d / "SKILL.md").is_file() and d.name not in declared:
                errs.append(f"skills: on-disk skill '{d.name}' is not declared in skills[]")

    kb = data.get("kb") or {}
    if not isinstance(kb, dict):
        errs.append("kb must be a mapping")
        kb = {}
    for key in kb:
        if key not in KB_KEYS:
            errs.append(f"kb: unknown key '{key}'")
    for zone in (kb.get("zones") or []):
        if not isinstance(zone, dict):
            errs.append(f"kb.zones: entry {zone!r} must be a mapping")
            continue
        for key in zone:
            if key not in ("path", "owner_agent"):
                errs.append(f"kb.zones: unknown key '{key}'")
        if zone.get("owner_agent") and zone["owner_agent"] not in agent_names:
            errs.append(f"kb.zones: owner_agent '{zone['owner_agent']}' is not main or a declared agent")

    if errs:
        for e in errs:
            print(f"aos-cap: manifest: {e}", file=sys.stderr)
        sys.exit(Exit.MANIFEST_INVALID)
    return data


def skill_rows(cap_dir: Path) -> tuple[dict, list[dict]]:
    """(manifest, [{id, installed_name, used_by}]) for a validated capability."""
    cap_dir = Path(cap_dir).resolve()
    data = validated_manifest(cap_dir)
    prefix = effective_prefix(data, cap_dir.name)
    rows = [{"id": e["id"],
             "installed_name": installed_name(cap_dir.name, prefix, e["id"]),
             "used_by": list(e.get("used_by") or [])}
            for e in (data.get("skills") or [])]
    return data, rows


def agent_rows(cap_dir: Path) -> tuple[dict, list[dict]]:
    """(manifest, [{id, installed_name}]) — the agent twin of `skill_rows`.

    Agents are declared by their `agents/*.agent.yaml` files, not by a manifest list (no
    `agents:` key exists — rule of two), so the ids come from disk. A capability with no
    `agents/` directory gets an empty list, which is the common case and not an error."""
    cap_dir = Path(cap_dir).resolve()
    data = validated_manifest(cap_dir)
    prefix = effective_prefix(data, cap_dir.name)
    return data, [{"id": a, "installed_name": installed_name(cap_dir.name, prefix, a)}
                  for a in sorted(declared_agent_ids(cap_dir))]
