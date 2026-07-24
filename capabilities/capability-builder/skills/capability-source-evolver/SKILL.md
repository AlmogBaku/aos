---
name: capability-source-evolver
description: "Evolves a capability's SHIPPED SOURCE in the clone — for everyone, not one user. A small tweak lands directly; a change to what the capability owns or does re-runs a scoped version of capability-builder's research/design/approval flow. Use for upstream bug reports and change requests about an existing capability ('the drainer should also flag X' as a fix for all users), or when capability-lifecycle's capability-evolver routes a source-level ask here. Not for personalizing one user's install — that's capability-evolver (the overlay ledger) — and not for something new to build — that's capability-builder."
---

# capability-source-evolver

Boundary: this skill edits `capabilities/<id>/` in the clone (the shipped source,
version-bumped, for everyone). Changing how an installed capability behaves *for this
user* is `capability-evolver` (capability-lifecycle) — the overlay ledger, not the source.

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
  a package-level tweak: **whose package is it?** A capability the user authored
  (built here, or an importer draft) is theirs — edit it in the clone; it goes live
  on the next install/update. An **upstream-shipped** capability is not silently
  edited in the clone — that's fork drift, the exact thing the overlay exists to
  prevent: route it through the overlay if it's personalizable, otherwise draft the
  change and offer to open an upstream PR (applying it locally only if the user
  accepts the divergence knowingly). Either way: tell the user what changed and
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
