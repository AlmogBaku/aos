import re

from ..constants import (
    CAPABILITY_TAGS_ORDERED, DEGRADED_MODES, DEPENDS_KEYS, HOST_FEATURES_ORDERED,
    HOST_LEVELS_ORDERED, KB_KEYS_ORDERED, KB_ZONE_KEYS, MAIN_AGENT, MANIFEST_KEYS_ORDERED,
    CRON_KEYS_ORDERED, SKILL_ENTRY_KEYS_ORDERED, USES_ENTRY_KEYS_ORDERED,
)
from ..frontmatter import read_frontmatter
from .agents import agent_names

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
CRON = re.compile(r"^\S+ \S+ \S+ \S+ \S+$")


def check_manifests(ctx) -> None:
    for cap in ctx.caps:
        file = f"{cap.rel}/CAPABILITY.md"
        parsed = read_frontmatter(cap.dir / "CAPABILITY.md")
        if parsed.error or parsed.data is None:
            ctx.report("error", "manifest/parse", file,
                       parsed.error or "missing frontmatter")
            continue
        data = parsed.data

        # Rule of two, enforced mechanically: a field nobody specced is an error.
        for key in data:
            if key not in MANIFEST_KEYS_ORDERED:
                ctx.report("error", "manifest/unknown-key", file,
                           f'unknown frontmatter key "{key}" (ARCHITECTURE §2.2 — rule of two)')

        if data.get("id") != cap.id:
            ctx.report("error", "manifest/id", file,
                       f'id "{data.get("id")}" != directory name "{cap.id}"')
        if not SEMVER.match(_js_str(data.get("version"))):
            ctx.report("error", "manifest/version", file,
                       f'version "{_js_str(data.get("version"))}" is not x.y.z semver')
        tags = data.get("tags")
        if (not isinstance(tags, list) or not tags
                or any(t not in CAPABILITY_TAGS_ORDERED for t in tags)):
            ctx.report("error", "manifest/tags", file,
                       f"tags must be a non-empty subset of "
                       f"{{{', '.join(CAPABILITY_TAGS_ORDERED)}}}")
        summary = data.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            ctx.report("error", "manifest/summary", file, "summary is required (one line)")

        _check_depends(ctx, data.get("depends"), file)
        agents = agent_names(cap)
        _check_cron(ctx, data.get("cron"), cap, file, agents)
        _check_skills_bijection(ctx, data.get("skills"), cap, file)
        _check_kb(ctx, data.get("kb"), cap, file, agents)
        _check_uses(ctx, data, cap, file, agents)

        if not (cap.dir / "README.md").exists():
            ctx.report("error", "manifest/readme", file,
                       "README.md is required (humans + PR review, ARCHITECTURE §2.1)")
        # BUILD-GAPS G3: MOD.example.md is presence-paired with ONBOARDING.md.
        if (cap.dir / "ONBOARDING.md").exists() and not (cap.dir / "MOD.example.md").exists():
            ctx.report("error", "manifest/mod-example", file,
                       "ONBOARDING.md present but MOD.example.md missing (they are "
                       "presence-paired)")


def _js_str(value) -> str:
    """`String(x ?? '')` — how the manifest's version reads when it is absent or a number.
    A YAML `version: 1.0` parses as a float, and `1.0` must fail semver as a STRING rather
    than crash the regex."""
    if value is None:
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))     # JS prints 1.0 as "1"
    return str(value)


def _check_depends(ctx, depends, file) -> None:
    if depends is None:
        return
    for key in depends:
        if key not in DEPENDS_KEYS:
            ctx.report("error", "depends/unknown-key", file, f'unknown depends key "{key}"')
    for dep in depends.get("capabilities") or []:
        # Household resolution (§3.1): a personal capability may depend on a shipped one,
        # so a dependency counts if it exists in the linted root OR the kit root.
        roots = [ctx.root, *ctx.dep_roots]
        if not any((r / "capabilities" / str(dep) / "CAPABILITY.md").exists() for r in roots):
            ctx.report("error", "depends/capability", file,
                       f'depends on "{dep}" but capabilities/{dep}/CAPABILITY.md does not '
                       f"exist")
    for feature, level in (depends.get("host") or {}).items():
        if feature not in HOST_FEATURES_ORDERED:
            ctx.report("error", "depends/host-feature", file,
                       f'"{feature}" is not in the §5.2 host vocabulary '
                       f"{{{', '.join(HOST_FEATURES_ORDERED)}}}")
        if level not in HOST_LEVELS_ORDERED:
            ctx.report("error", "depends/host-level", file,
                       f'host level "{level}" must be one of '
                       f"{{{', '.join(HOST_LEVELS_ORDERED)}}}")


def _check_cron(ctx, jobs, cap, file, agents) -> None:
    if jobs is None:
        return
    seen = set()
    for s in jobs:
        s = s if isinstance(s, dict) else {}
        sid = s.get("id")
        for key in s:
            if key not in CRON_KEYS_ORDERED:
                ctx.report("error", "cron/unknown-key", file,
                           f'cron job "{_u(sid)}": unknown key "{key}"')
        if not sid or sid in seen:
            ctx.report("error", "cron/id", file,
                       f'cron job id "{_u(sid)}" missing or duplicate')
        seen.add(sid)
        if not CRON.match(_js_str(s.get("expr"))):
            ctx.report("error", "cron/expr", file,
                       f'cron job "{_u(sid)}": expr "{_u(s.get("expr"))}" is not a 5-field '
                       f"expression")
        # §2.2: exec (mechanical, deterministic-only) XOR agent+prompt_ref (judgment).
        has_exec = s.get("exec") is not None
        has_agent = s.get("agent") is not None or s.get("prompt_ref") is not None
        if has_exec and has_agent:
            ctx.report("error", "cron/exec-xor-agent", file,
                       f'cron job "{_u(sid)}": exec and agent/prompt_ref are mutually '
                       f"exclusive")
        elif has_exec:
            # First token: a capability-relative path (must resolve) or a bare command
            # (no slash) provided by the capability's tool install (§2.4 — the briefing
            # documents the install; the cheat-sheet wires the degraded form).
            exec_tok = _js_str(s.get("exec")).split(" ")[0]
            if "/" in exec_tok and not (cap.dir / exec_tok).exists():
                ctx.report("error", "cron/exec-ref", file,
                           f'cron job "{_u(sid)}": exec "{exec_tok}" does not resolve inside '
                           f"the capability")
        else:
            if s.get("agent") != MAIN_AGENT and s.get("agent") not in agents:
                ctx.report("error", "cron/agent", file,
                           f'cron job "{_u(sid)}": agent "{_u(s.get("agent"))}" is neither '
                           f'"{MAIN_AGENT}" nor a declared agents/*.agent.yaml name')
            prompt_ref = s.get("prompt_ref")
            if not prompt_ref or not (cap.dir / str(prompt_ref)).exists():
                ctx.report("error", "cron/prompt-ref", file,
                           f'cron job "{_u(sid)}": prompt_ref "{_u(prompt_ref)}" does not '
                           f"resolve inside the capability")
        if s.get("degraded") not in DEGRADED_MODES:
            ctx.report("error", "cron/degraded", file,
                       f'cron job "{_u(sid)}": degraded "{_u(s.get("degraded"))}" must be one '
                       f"of {{{', '.join(DEGRADED_MODES)}}}")


def _u(value) -> str:
    """A missing field interpolates as `undefined` in the JS messages, not as `None`. The
    oracle pins that text, and a message shape is what a fixture assertion reads."""
    return "undefined" if value is None else str(value)


def _check_skills_bijection(ctx, skills, cap, file) -> None:
    declared = set()
    for s in skills or []:
        s = s if isinstance(s, dict) else {}
        for key in s:
            if key not in SKILL_ENTRY_KEYS_ORDERED:
                ctx.report("error", "skills/unknown-key", file,
                           f'skill "{_u(s.get("id"))}": unknown key "{key}"')
        declared.add(s.get("id"))
        if not (cap.dir / "skills" / str(s.get("id")) / "SKILL.md").exists():
            ctx.report("error", "skills/missing-dir", file,
                       f'declared skill "{_u(s.get("id"))}" has no skills/'
                       f"{_u(s.get('id'))}/SKILL.md")
    skills_dir = cap.dir / "skills"
    if skills_dir.exists():
        on_disk = [d.name for d in sorted(skills_dir.iterdir(), key=lambda p: p.name)
                   if d.is_dir()]
        for skill_id in on_disk:
            if skill_id not in declared:
                ctx.report("error", "skills/undeclared", file,
                           f"skills/{skill_id}/ exists but is not declared in the manifest "
                           f"skills[] list")


def _check_kb(ctx, kb, cap, file, agents) -> None:
    if kb is None:
        return
    for key in kb:
        if key not in KB_KEYS_ORDERED:
            ctx.report("error", "kb/unknown-key", file, f'unknown kb key "{key}"')
    for zone in kb.get("zones") or []:
        zone = zone if isinstance(zone, dict) else {}
        for key in zone:
            if key not in KB_ZONE_KEYS:
                ctx.report("error", "kb/zone-key", file,
                           f'kb zone "{_u(zone.get("path"))}": unknown key "{key}"')
        if zone.get("owner_agent") != MAIN_AGENT and zone.get("owner_agent") not in agents:
            ctx.report("error", "kb/owner-agent", file,
                       f'kb zone "{_u(zone.get("path"))}": owner_agent '
                       f'"{_u(zone.get("owner_agent"))}" does not resolve')


def _check_uses(ctx, data, cap, file, agents) -> None:
    """`uses` (RFC-009 option 2): one of this capability's agents loads a skill another
    capability ships. Same rules as `aos-cap manifest`, so CI and the installer agree: the
    provider is a dependency, it declares the skill, and the grantee is main or our agent."""
    uses = data.get("uses")
    if uses is None:
        return
    if not isinstance(uses, list):
        ctx.report("error", "uses/shape", file,
                   "uses must be a list of {capability, skill, agents} mappings")
        return
    deps = {str(d) for d in ((data.get("depends") or {}).get("capabilities") or [])}
    seen = set()
    for entry in uses:
        if not isinstance(entry, dict):
            ctx.report("error", "uses/shape", file, f"uses entry {entry!r} must be a mapping")
            continue
        for key in entry:
            if key not in USES_ENTRY_KEYS_ORDERED:
                ctx.report("error", "uses/unknown-key", file,
                           f'unknown uses key "{key}" (one of '
                           f"{', '.join(USES_ENTRY_KEYS_ORDERED)})")
        prov, skill, grantees = entry.get("capability"), entry.get("skill"), entry.get("agents")
        if (prov, skill) in seen:
            ctx.report("error", "uses/duplicate", file,
                       f"uses names {prov}/{skill} twice — merge the agents lists")
        seen.add((prov, skill))
        if prov == cap.id or str(prov) not in deps:
            ctx.report("error", "uses/capability", file,
                       f'uses capability "{prov}" must be another capability listed in '
                       f"depends.capabilities (own skills are scoped with used_by)")
        else:
            provider = next((r / "capabilities" / str(prov) for r in [ctx.root, *ctx.dep_roots]
                             if (r / "capabilities" / str(prov) / "CAPABILITY.md").exists()), None)
            if provider is not None:
                pm = read_frontmatter(provider / "CAPABILITY.md").data or {}
                ids = {e.get("id") for e in (pm.get("skills") or []) if isinstance(e, dict)}
                if skill not in ids:
                    ctx.report("error", "uses/skill", file,
                               f'"{prov}" declares no skill "{skill}"')
        if not isinstance(grantees, list) or not grantees:
            ctx.report("error", "uses/agents", file,
                       f"uses {prov}/{skill}: agents must be a non-empty list")
        else:
            for a in grantees:
                if a != MAIN_AGENT and a not in agents:
                    ctx.report("error", "uses/agents", file,
                               f'uses {prov}/{skill}: agent "{a}" is neither "main" nor a '
                               f"declared agent")
