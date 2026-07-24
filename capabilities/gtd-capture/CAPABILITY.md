---
id: gtd-capture
version: 0.2.0
tags: [usecase]
summary: Voice/text → instant capture into kb's raw/captures/; a nightly drain turns pending captures into next-actions and reminders.
depends:
  capabilities: [kb, onboarding]
  host:
    cron: preferred
    messaging.inbound: required
    messaging.outbound: preferred
skills:
  - id: gtd-capture
    used_by: [main, drainer]
  - id: capture
    used_by: [main]
  - id: drain
    used_by: [drainer]
schedules:
  - id: nightly-drain
    cron: "0 23 * * *"
    agent: drainer
    prompt_ref: agents/drainer/nightly-drain.md
    degraded: manual
kb:
  zones:
    - path: "_ops/next-actions.md"
      owner_agent: drainer
    - path: "raw/captures/**"
      owner_agent: drainer
    - path: "projects/**"
      owner_agent: drainer
---

# gtd-capture — installer's briefing

*(This document is consumed at install and not used afterwards. The runtime face of
the capability is the `gtd-capture` entry skill.)*

## What this is

The first usecase capability built on kb's engine — proof that a capability can build
entirely on zones kb already declares rather than inventing its own. Capture is dumb
and fast (no synchronous classification, under 5 seconds); a nightly drain does the GTD
thinking, walking kb's own pending view instead of a capability-owned inbox file.

## What you materialize, and why

1. **Skills** per `used_by`: the `gtd-capture` entry skill goes to the front agent AND
   the drainer — it carries the map. `capture` is the front agent's write path (composes
   with kb's `route` skill, never the front agent's own routing logic). `drain` is the
   drainer's judgment skill — it also stays real and loadable rather than folding into
   the schedule prompt, because it's user-triggerable ad hoc ("drain the inbox now"),
   not only the nightly job.
2. **The drainer agent** (`agents/drainer.agent.yaml`): create per the cheat-sheet. Its
   prompt body lives at `agents/drainer/nightly-drain.md`.
3. **Schedule — in the same session as the base it drains, never deferred.**
   `nightly-drain` defaults to 23:00; the user's `drain_hour` answer overrides the cron
   at materialization. **It must run before kb's own 23:30 `nightly-promote`** — drain's
   GTD read of a pending capture has to happen before the archiver's later promote step
   flips that capture's `triage` to `done`/`failed`. Degrades to `manual` without cron.
4. **Zones — rows into kb's existing zones, never a new directory.** Three drainer
   grant rows, appended to each base's Grants table at install (user-approved diff),
   each with `via: gtd-capture@<version>` — exactly that format, one capability per
   row (revocation deletes rows by via match):
   - `_ops/next-actions.md` · write · notes: "standalone next-actions, GTD nightly
     drain" (template in `kb/zones/`).
   - `raw/captures/**` · write · notes: "additive frontmatter bookkeeping only —
     meta.gtd_triaged; never the triage field".
   - `projects/**` · write · notes: "next_action frontmatter field only".
   Also at install, per target base: propose adding **`next_action` to that base's
   `BASE.yaml frontmatter.extensions`** (a schema change — owner-approved in the same
   diff) so the field the drainer maintains is schema-legal, not a lint finding.
   Project-linked next-actions live in the owning project page's `next_action`
   frontmatter field — a kb-owned mechanism this capability updates under that grant,
   never redeclares. The front agent's ability to create raw captures
   (`route-into raw/captures/**`) already comes free from kb's own install —
   gtd-capture doesn't redeclare that grant. **On a shared base**, register only the
   `raw/captures/**` bookkeeping row: drain never writes next-actions directly into a
   repo colleagues pull — its judgment outputs land as `_ops/needs-review.md`
   proposals there (same posture as kb's archiver).
5. **Onboarding** asks capture channels, reminder target, drain hour, and next-action
   phrasing; answers fill the capture skill's `{{mod: capture_preferences}}` slot and
   drive the schedule and drain behavior.

## Contracts to preserve

- Capture never classifies synchronously, never dedups, never formats — that's the
  tool's (`base capture`) and kb's `route` skill's job, not this capability's.
- Drain's pass is additive only: it files next-actions/reminders and marks its own pass
  via `meta.gtd_triaged` (the schema's free per-doc escape hatch) — it never flips a
  capture's own `triage` field. That stays kb's archiver's call.
- Ordering is a contract, not a convenience: drain (23:00) runs before kb's promote
  (23:30), every night, on every base either touches.

## Contested core — none

gtd-capture takes no position on RFC-006 (multi-KB routing/authorization) — it consumes
kb's `route` skill as-is and defers entirely to kb's contract.
