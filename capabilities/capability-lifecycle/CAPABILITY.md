---
id: capability-lifecycle
version: 0.2.0
tags: [infra]
summary: The capability lifecycle as a capability — install, upgrade, remove, and evolve skills for the front agent, the MOD.md overlay with its promote/retire exit side, the household layout with pinned renders and symlink installs, the per-harness cheat-sheets, and the aos-lock bookkeeping tool that owns the lockfile.
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
The household is already in place when you get here (BOOTSTRAP §1): `<home>/upstream`
this clone, `<home>/personal` the user's private repo, `<home>/.aos` machine state.

## What you materialize

1. **The `aos-lock` tool first**:
   `uv tool install --from <home>/upstream/capabilities/capability-lifecycle/tool aos-lock`
   (`uv` is a hard bootstrap prerequisite). Then `aos-lock --home <home> init` creates
   the lockfile — the tool's file from this moment on; you call verbs, you never edit
   the YAML.
2. **All five skills to the front agent** (`used_by: [main]` throughout), per your
   cheat-sheet (`harnesses/<harness-runtime>.md` in this capability; none for your
   harness → the entry skill's `reference/no-cheatsheet.md`). The skills are
   `{{mod}}`-slot-free — no transform: a mechanical render into
   `personal/capabilities/capability-lifecycle/skills/…` (committed) plus symlinks into
   the front agent's skills dir, under the `reference/contract.md` rules (read it in
   full before this step: household resolution, naming, provenance,
   STAGE→GATE→EXECUTE, the persist hook).
3. Nothing else: no agents, no schedules, no KB zones, no interview (this capability has
   no personalization — it ships neither ONBOARDING.md nor MOD.example.md by design).

## Why it is shaped this way

- The five skills are the runtime face of ARCHITECTURE §5 and design/install-flow.md
  §2–§4; the entry skill (`capability-lifecycle`) carries the shared depth
  (`reference/`) and the Experience rules every lifecycle interaction obeys.
- The evolver is a **two-way door**: personalization flows in (the MOD), and
  generally-useful mechanism flows out (promotion, signal-gated; retirement closes the
  loop when upstream absorbs a line) — the judgment lives once, in the entry skill's
  `reference/overlay.md`.
- Renders are **pinned** (committed in `personal/`) because the transform is agentic:
  the commit is the render's lockfile, upgrades review as a git diff, and rollback is
  `git revert`. Harnesses symlink to the one canonical render — never copies.
- Skill ids are deliberately verbose (`capability-installer`, not `install`): they land
  among dozens of other skills, and a name must carry its meaning out of context (§2.5).
- The cheat-sheets live here because these skills are their only consumer; each is lean —
  the harness half only — and points back at `reference/contract.md` for the aos half.
- `aos-lock` is deterministic bookkeeping only (§2.4): manifest parse/validate + lockfile
  verbs (now including link records and source roots). Judgment stays with you; hashes
  never do.

## Removal

`aos-lock show capability-lifecycle` → delete the five skill symlinks, then the render
dirs in `personal/` via a commit → `uv tool uninstall aos-lock` → the lockfile entry is
the last thing standing; removing this capability last (after every other capability is
removed) is the only safe order — the other removals need its skills and tool.
