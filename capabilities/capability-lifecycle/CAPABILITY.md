---
id: capability-lifecycle
version: 0.1.0
tags: [infra]
summary: The capability lifecycle as a capability — install, upgrade, remove, and evolve skills for the front agent, the MOD.md overlay ledger, the per-harness cheat-sheets, and the aos-lock bookkeeping tool that owns the lockfile.
skills:
  - id: capability-lifecycle
    used_by: [main]
  - id: capability-installer
    used_by: [main]
  - id: capability-upgrader
    used_by: [main]
  - id: capability-remover
    used_by: [main]
  - id: capability-evolver
    used_by: [main]
---

# capability-lifecycle — the installer's briefing

You are reading this at bootstrap, installing the capability that will make every later
install a skill. This is the only capability `BOOTSTRAP.md` installs inline (the
chicken-and-egg break); everything else goes through `capability-installer` afterwards.

## What you materialize

1. **The `aos-lock` tool first**: `uv tool install --from <clone>/capabilities/capability-lifecycle/tool aos-lock`
   (`uv` is a hard bootstrap prerequisite). Then `aos-lock init` creates the lockfile —
   the tool's file from this moment on; you call verbs, you never edit the YAML.
2. **All five skills to the front agent** (`used_by: [main]` throughout), per your
   cheat-sheet (`harnesses/<harness-runtime>.md` in this capability; none for your
   harness → the entry skill's `reference/no-cheatsheet.md`). The skills are
   `{{mod}}`-slot-free — no transform, a mechanical copy under the
   `reference/contract.md` rules (read it in full before this step: naming, provenance,
   STAGE→GATE→EXECUTE).
3. Nothing else: no agents, no schedules, no KB zones, no interview (this capability has
   no personalization — it ships neither ONBOARDING.md nor MOD.example.md by design).

## Why it is shaped this way

- The five skills are the runtime face of ARCHITECTURE §5 and design/install-flow.md
  §2–§4; the entry skill (`capability-lifecycle`) carries the shared depth
  (`reference/`) and the Experience rules every lifecycle interaction obeys.
- Skill ids are deliberately verbose (`capability-installer`, not `install`): they land
  among dozens of other skills, and a name must carry its meaning out of context (§2.5).
- The cheat-sheets live here because these skills are their only consumer; each is lean —
  the harness half only — and points back at `reference/contract.md` for the aos half.
- `aos-lock` is deterministic bookkeeping only (§2.4): manifest parse/validate + lockfile
  verbs. Judgment stays with you; hashes never do.

## Removal

`aos-lock show capability-lifecycle` → delete the five materialized skill dirs →
`uv tool uninstall aos-lock` → the lockfile entry is the last thing standing; removing
this capability last (after every other capability is removed) is the only safe order —
the other removals need its skills and tool.
