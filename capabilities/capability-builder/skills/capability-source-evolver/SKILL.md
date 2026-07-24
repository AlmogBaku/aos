---
name: capability-source-evolver
description: "Evolves a capability's SHIPPED SOURCE — for everyone, not one user. A small tweak lands directly; a change to what the capability owns or does re-runs a scoped version of capability-builder's research/design/approval flow. Use for upstream bug reports and change requests about an existing capability ('the drainer should also flag X' as a fix for all users), when capability-lifecycle's capability-evolver routes a source-level ask or a promotion here ('promote this MOD line', 'this should be for everyone'), or when a contribution needs drafting for upstream. Not for personalizing one user's install — that's capability-evolver (the overlay ledger) — and not for something new to build — that's capability-builder."
---

# capability-source-evolver

Boundary: this skill edits capability *source* — for everyone who uses the package.
Whose package decides where that is: the user's own capabilities live in
`<home>/personal/capabilities/<id>/` (theirs — edit directly); upstream-shipped ones
live in `<home>/upstream/capabilities/<id>/` and are **never silently edited** — changes
to them are contributions, drafted on a branch. Changing how an installed capability
behaves *for this user* is `capability-evolver` (capability-lifecycle) — the overlay
ledger, not the source.

**Hard invariant: you never open a PR, file an issue, +1, push, fork, or create a
remote branch — for upstream or any repo the user doesn't own — without the user's
explicit approval or request.** You draft and offer; only the user
sends. `gh pr create` / `gh issue create` confirm once more before firing.

**Invariant: the size of the change decides the ceremony, not the size of the ask.**
Classify before acting — see [reference/judgment.md](reference/judgment.md).

## Intakes

- **A source fix** ("the drainer double-counts") — classify Small/Major below.
- **A promotion** (routed from `capability-evolver` with a ledger line, or "promote
  this"): extract the *mechanism* — the user's literal nuance text never ships. A
  missing knob becomes a `{{mod: <key>}}` slot at the site the nuance targets **plus**
  the matching `ONBOARDING.md` question **plus** a `MOD.example.md` placeholder
  (the three land together; ONBOARDING and MOD.example are presence-paired). Tell the
  user: their concrete answer stays in their MOD; once the upstream change lands in an
  upgrade, the ledger line retires. Generality uncertain → the lightest rung is a
  signal issue, not a PR (the ledger search and issue-first path are in
  [reference/contribute.md](reference/contribute.md)).

## Classify

- **Small** — wording, a threshold, a personalization answer, a knob promotion; no new
  file beyond the knob's question/placeholder, no schema/contract change, doesn't
  change what the capability owns.
- **Major** — a new skill/agent/schedule/kb-zone, a schema or contract change, changes
  what the capability owns or is responsible for.

Judgment call — [reference/judgment.md](reference/judgment.md) has worked examples to
calibrate against, not a checklist to satisfy mechanically.

## Then

- **Small**: apply where the feedback actually lives, and make it take effect now —
  a personalization answer changes through the onboarding skill (the only MOD.md
  writer), then the live render is synced to match (the §3.3 round-trip: overlay and
  install stay consistent, MOD.md stays the source of truth);
  a package-level tweak: **whose package is it?** The user's own
  (`personal/capabilities/`, built here or an importer draft) — edit it directly; it
  goes live on the next install/update. **Upstream-shipped** — draft the change on a
  branch and *offer* the contribution per
  [reference/contribute.md](reference/contribute.md) (applying it locally only if the
  user accepts the divergence knowingly, as a dated ledger workaround that retires
  when the PR lands). Either way: tell the user what changed and where — transparent,
  not silent, but no approval gate for their own package.
- **Major**: interrupt like `capability-builder`'s detector does, then run the
  scaled-down procedure in [reference/procedure.md](reference/procedure.md).

## Authority

- May freely: classify, apply a small change to the *user's own* packages (via
  onboarding for answers, `personal/` edits for package tweaks), sync the live render
  a changed answer personalizes, draft branches/PR bodies/issues, tell the user what
  changed.
- Report-only: what changed and where, for small edits.
- Ask first: anything classified major (research/design/approval before it applies,
  same gate as a new capability's Build stage) — and **every** write that leaves the
  machine toward upstream: PRs, issues, +1s, pushes. No exceptions.
