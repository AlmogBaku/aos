---
name: capability-builder
description: "Detects when a request has drifted from a one-off task into building something persistent (a new skill, agent, cron, or standing automation) and offers to plan it properly before anything gets built. Use BEFORE creating any cron job, scheduled task, recurring reminder, or standing automation — whenever the user describes something recurring or systemic: 'every morning/day/weekday at <time>, do X', 'send me a daily/weekly summary or digest', 'remind me every...', 'let's build something that...', 'can we make it so every time X, Y', 'watch X and do Y when...', 'I keep doing this manually, can we automate it', or an explicit ask for a new skill/agent/cron/capability. Not for one-off asks even if phrased with add/create/make ('add this to my calendar', 'create a file called notes.md') and not for feedback on a capability that already exists — that's evolve-capability."
---

# capability-builder — the detector

**Invariant: nothing durable gets written without the user's explicit approval of a
design.** Research is investigative; only the approved Build stage writes.

## The interrupt

The moment the trigger fires: say plainly what you noticed, then ask —

> Hey, should we plan this methodically?

If declined: back off for this request, let operating mode continue, don't repeat the
ask on the same request. If the same shape of ask resurfaces later, you can offer
again — this is per-request suppression, not a permanent opt-out.

Calibration: fire on *use-case*-shaped language (recurring, systemic, creates
persistent behavior), never on *task*-shaped language even when it says
add/create/make. See [reference/trigger-patterns.md](reference/trigger-patterns.md)
for worked examples.

Feedback on a capability that's already installed is a different signal — that's
`evolve-capability`, not this flow.

## If the user agrees: the procedure

Copy this checklist and work the stages in order — **stop for the user between each**:

```
- [ ] 1. Intake    — reference/intake.md
- [ ] 2. Research  — reference/research.md
- [ ] 3. Design    — reference/design.md — THE approval gate; nothing after this
                      stage runs until the user explicitly signs off
- [ ] 4. Build     — reference/build.md
```

## Authority

- May freely: notice the trigger, ask the interrupt question, run intake questions,
  spawn research subagents, draft the design proposal.
- Report-only: research findings, gaps, anything the design proposal flags as
  uncertain — surfaced in the proposal, never resolved silently.
- Ask first: the design itself — nothing proceeds to Build without explicit approval —
  and anything touching the live harness (out of scope for this skill: Build only ever
  writes into `capabilities/<id>/` in the user's clone, same as `importer`; installing
  what gets built is the separate, already-specified install flow).
