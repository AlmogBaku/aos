---
name: build
description: "Detects when a request has drifted from a one-off task into building something persistent (a new skill, agent, cron, or standing automation) and offers to plan it properly before anything gets built. Use BEFORE creating any cron job, scheduled task, recurring reminder, or standing automation — whenever the user describes something recurring or systemic: 'every morning/day/weekday at some time, do X', 'send me a daily/weekly summary or digest', 'remind me every...', 'let's build something that...', 'can we make it so every time X, Y', 'watch X and do Y when...', 'I keep doing this manually, can we automate it', or an explicit ask for a new skill/agent/cron/capability. Not for one-off asks even if phrased with add/create/make ('add this to my calendar', 'create a file called notes.md') and not for feedback on a capability that already exists — that's capability-contribute (source-level) or capability-evolve (one user's install)."
---

# capability-build — the detector

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
{{skill: contribute}}, not this flow.

## If the user agrees: the procedure

**Branch the session first** — if your harness can branch a conversation (your
cheat-sheet's `mapping.session`, its `branch`), hand the user its command
and continue once they are in the branch: every stage below runs there, and the original
session stays where they left their work. No `branch`, or `support: none` → say so in one
line and continue in place.

**Then enter plan mode** — if your harness has a native plan/read-only mode
(`mapping.plan_mode`), enter it now; if not, enforce it as prose: no writes anywhere until
the Design approval gate. Exit plan mode only at that gate. Copy this checklist and work the stages
in order — **stop for the user between each**:

```
- [ ] 1. Intake     — reference/intake.md
- [ ] 2. Research   — reference/research.md
- [ ] 3. Design     — reference/design.md — THE approval gate; nothing after this
                       stage runs until the user explicitly signs off
- [ ] 4. Build      — reference/build.md
- [ ] 5. Hand back  — reference/build.md, "Hand back": the way back to the interrupted
                       work, and what must reload to see what was built
```

## Authority

- May freely: notice the trigger, ask the interrupt question, run intake questions,
  spawn research subagents, draft the design proposal.
- Report-only: research findings, gaps, anything the design proposal flags as
  uncertain — surfaced in the proposal, never resolved silently.
- Ask first: the design itself — nothing proceeds to Build without explicit approval —
  every write toward upstream (the contribute question's yes starts a flow whose PR
  still opens only on explicit confirm; never any PR/issue/push without it), and
  anything touching the live harness (out of scope for this skill: Build only ever
  writes into `<aos_home>/personal/capabilities/<id>/`, same as {{skill: import}}; installing
  what gets built is the separate, already-specified install flow).
