---
id: capability-builder
version: 0.1.0
tags: [infra]
summary: Detects use-case-shaped requests mid-conversation and turns them into an intake -> research -> design -> approval -> build procedure instead of ad hoc changes; also evolves capabilities that already exist.
depends:
  capabilities: [onboarding]
skills:
  - id: capability-builder
    used_by: [main]
  - id: evolve-capability
    used_by: [main]
---

# capability-builder — installer's briefing

*(This document is consumed at install and not used afterwards. The runtime face of
the capability is the `capability-builder` entry skill.)*

## What this is

The building-mode boundary from MARS — the Mode-Aware Runtime System pattern:
operating mode handles requests, building mode designs capabilities, and the runtime
enforces the line between them (ARCHITECTURE §9). Concretely: a detector that notices when a
conversational request has drifted from a one-off task into a use-case-shaped ask —
something that would create persistent, unattended state (a skill, a schedule, an
agent, a standing automation) — and forces a higher-ceremony path before anything
durable gets written: intake, research, a single proposal the user must approve, then
build. Also handles feedback on capabilities that already exist, scaled to how much the
change actually touches.

## What you materialize, and why

1. **The `capability-builder` entry skill** — the detector plus the whole
   new-capability procedure (intake/research/design/build), each a `reference/` stage
   doc in the same folder. One skill, not two: the procedure never fires on its own,
   only ever as a continuation after the detector interrupts and the user agrees, so
   splitting it into its own skill folder would add a boundary that isn't doing work.
2. **The `evolve-capability` skill** — feedback on a capability that's already
   installed. Kept separate: unlike the procedure above, it has its own independent
   trigger — a user can reach it without ever passing through the detector.
3. **The mode-boundary context block** — a short, marker-delimited append to the
   front agent's identity context (on Hermes: `SOUL.md`), stating: before creating
   any cron job, scheduled task, recurring reminder, persona, or standing automation
   in response to a conversational request, follow the `capability-builder` skill —
   interrupt first, proceed ad hoc only if the user declines. This block is the
   detector's teeth: a skill description is pull-context (consulted only when the
   model thinks to), but a harness with a native cron tool will satisfy a
   schedule-shaped ask the shortest way and never consult it — the boundary must be
   push-context, always present. Found the hard way in the first live e2e. Canonical
   block text (materialize verbatim, inside the usual `aos:capability-builder@<ver>`
   markers):

   > Mode boundary (MARS): before creating any cron job, scheduled task, recurring
   > reminder, persona, or standing automation in response to a conversational
   > request, stop and follow the `capability-builder` skill — say what you noticed
   > and ask "Hey, should we plan it methodically?" first. Proceed ad hoc only if
   > the user declines. One-off tasks are unaffected.
4. Both skills go to the front agent only — no agents, no schedules, no `kb` block.
   Every skill scoped to `main` trips the linter's `skill/all-main` warning; that's
   deliberate here (no dedicated "builder" agent — see Contracts), not an oversight.

## Contracts to preserve

- Building mode is a procedural mode-switch `main` enforces on itself, not a separate
  materialized agent/profile — no harness here exposes a live conversation-handoff
  primitive, so the boundary lives in prompt-level instruction (the always-present
  context block plus the skills), not a process boundary.
- Never writes a capability's files without an explicit, user-approved design. Research
  subagents are investigative only — nothing but the approved Build stage writes.
- Package materialization (Build, and evolve's major Apply) never installs into the
  harness and never opens a PR — output is a capability package in the user's clone,
  same invariant as `importer`; the already-specified install flow picks it up from
  there, and the user is told so. Evolve's small path is the one exception by design:
  it adjusts the user's own overlay answers (through the onboarding skill, the only
  MOD.md writer) and syncs the live artifact those answers personalize — the §3.3
  round-trip, not an install.
- Nothing personal lands in a shippable file — intake nuance splits into the
  package's interview questions and the user's own MOD.md, exactly like the
  importer's mechanism/nuance split, just in reverse.
- The detector fires on use-case-shaped language (recurring, systemic, "build me
  something that persists") and never on one-off task language, even when the wording
  contains add/create/make — gating everything trains the user to stop reading what
  they approve, which defeats the point.
- Small evolve-feedback is applied directly and summarized afterward, never silently.
  Major evolve-feedback re-runs the research/design/approval shape, scaled down.
