from ..constants import MAIN_AGENT, SKILL_SLOT
from ..frontmatter import read_frontmatter


# A `{{skill: other/x}}` slot NAMES a foreign skill; it does not put that skill where the
# agent reading the file can load it. A non-main agent's skills folder holds only what is
# linked into it, so without a `uses` grant the reference resolves to nothing at runtime —
# the shape of a consumer whose provider's upgrade relinked per its own `used_by` and left
# the consumer's cron jobs failing silently. Files also reached by `main` stay silent: main
# composes through the provider's own `used_by: [main]` link (the routing hint pattern).
def check_uses_reach(ctx) -> None:
    for cap in ctx.caps:
        manifest = read_frontmatter(cap.dir / "CAPABILITY.md").data or {}
        reach: dict[str, set] = {}
        for entry in manifest.get("skills") or []:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                continue
            scope = f"{cap.rel}/skills/{entry['id']}/"
            for file in ctx.files:
                if file.startswith(scope) and file.endswith(".md"):
                    reach.setdefault(file, set()).update(
                        str(a) for a in (entry.get("used_by") or []))
        for sched in manifest.get("schedules") or []:
            if isinstance(sched, dict) and isinstance(sched.get("prompt_ref"), str) \
                    and sched.get("agent"):
                reach.setdefault(f"{cap.rel}/{sched['prompt_ref']}", set()).add(
                    str(sched["agent"]))

        grants: dict[tuple, set] = {}
        for u in manifest.get("uses") or []:
            if isinstance(u, dict):
                grants.setdefault((u.get("capability"), u.get("skill")), set()).update(
                    str(a) for a in (u.get("agents") or []))

        for file, agents in sorted(reach.items()):
            if MAIN_AGENT in agents:
                continue
            try:
                text = (ctx.root / file).read_text(encoding="utf-8")
            except OSError:
                continue
            for i, line in enumerate(text.split("\n")):
                for m in SKILL_SLOT.finditer(line):
                    prov, skill = m.group(1), m.group(2)
                    if skill is None or prov == cap.id:
                        continue
                    for agent in sorted(agents - grants.get((prov, skill), set())):
                        ctx.report("error", "uses/missing", f"{file}:{i + 1}",
                                   f'{m.group(0)} is loaded by agent "{agent}", which cannot '
                                   f"reach another capability's skill without a grant — "
                                   f"declare uses: [{{capability: {prov}, skill: {skill}, "
                                   f"agents: [{agent}]}}]")
