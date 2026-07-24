---
name: evolve-capability
description: "Applies feedback to a capability that's already installed — a small tweak lands directly, a change to what the capability owns or does re-runs a scoped version of capability-builder's research/design/approval flow. Use when the user gives feedback, a bug report, or a change request about a capability that already exists ('the drainer should also flag X', 'can capture also do Y'). Not for describing something new to build — that's capability-builder."
---

# evolve-capability

**Invariant: the size of the change decides the ceremony, not the size of the ask.**
Classify before acting — see [reference/judgment.md](reference/judgment.md).

## Classify

- **Small** — wording, a threshold, a personalization answer; no new file, no
  schema/contract change, doesn't change what the capability owns.
- **Major** — a new skill/agent/schedule/kb-zone, a schema or contract change, changes
  what the capability owns or is responsible for.

Judgment call — [reference/judgment.md](reference/judgment.md) has worked examples to
calibrate against, not a checklist to satisfy mechanically.

## Then

- **Small**: apply where the feedback actually lives, and make it take effect now —
  a personalization answer changes through the onboarding skill (the only MOD.md
  writer), then the live materialized artifact is synced to match (the §3.3
  round-trip: overlay and install stay consistent, MOD.md stays the source of truth);
  a package-level tweak edits the capability in the clone, and the user is told it
  goes live on the next install/update. Either way: tell the user what changed and
  where — transparent, not silent, but no approval gate.
- **Major**: interrupt like `capability-builder`'s detector does, then run the
  scaled-down procedure in [reference/procedure.md](reference/procedure.md).

## Authority

- May freely: classify, apply a small change (via onboarding for answers, clone edits
  for package tweaks), sync the live artifact a changed answer personalizes, tell the
  user what changed.
- Report-only: what changed and where, for small edits.
- Ask first: anything classified major — research/design/approval before it applies,
  same gate as a new capability's Build stage.
