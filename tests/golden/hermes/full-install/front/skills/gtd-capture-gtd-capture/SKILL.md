---
x-aos-origin: gtd-capture@0.2.0
name: gtd-capture
description: "The capture-to-drain front door — fire off a thought, run tonight's GTD triage, or ask where captures/next-actions stand. Use when firing off a quick thought/task/idea to capture, running or asking about the nightly drain, or any mention of 'capture', 'inbox', 'drain', 'next-action', or GTD triage."
---

# gtd-capture — capture is dumb, drain does the thinking

**Invariant: capture never classifies.** A thought lands as a raw file in under 5
seconds; all judgment happens later, in one nightly pass.

## The mental model

- **Capture** — the `capture` skill composes with kb's `route` skill to write one raw
  file per thought via `base capture` (instant, deduped, `triage: pending`). No
  lookups, no clarifying questions, no next-action decision on this path.
- **Drain** — the nightly GTD triage (`drain` skill, default 23:00; the user's
  `drain_hour` answer overrides the cron) walks kb's own pending view and turns
  actionable captures into next-actions, reminders, or two-minute-done. Its pass is
  additive only — it never flips a capture's own `triage` field.
- **kb's own archiver** separately promotes raw captures into wiki knowledge 30 minutes
  later (23:30, `nightly-promote`). Ordering is unchanged and still matters: drain must
  run first, so its GTD read of a capture happens before the archiver's promote step
  changes that capture's `triage` to `done`/`failed`.

## Where things live

- `raw/captures/**` — every capture, kb's own zone. The pending view is `base inbox`
  (and `base inbox --failed` for previously-failed items needing attention) — never a
  hand-rolled file.
- Project-linked next-actions — the owning project page's `next_action` frontmatter
  field (kb's own mechanism; gtd-capture reads and updates it, never redeclares it).
- Standalone next-actions (no owning project) — `_ops/next-actions.md`, a grant into
  kb's existing `_ops/` zone owned by the drainer. Not a zone of gtd-capture's own.

## Which skill for which job

| Job | Skill |
|---|---|
| Fire off a capture | `capture` |
| Nightly triage / "drain the inbox now" | `drain` |
| What capture composes, corrections rule | `reference/entry-format.md` here |

## Authority

- May freely (front agent): capture, any time, no lookups first.
- May freely (drainer): read `base inbox` / `base inbox --failed`; write/update
  `_ops/next-actions.md` and a project's `next_action` field; write `meta.gtd_triaged`
  on a raw capture (additive bookkeeping only).
- Never: flip a capture's own `triage` field (that stays kb's archiver's call, at its
  later promote step) or delete/edit a raw capture's other frontmatter.
- Degrades to manual: the drain schedule without cron becomes an invocable run-card;
  the capture path has no degraded mode — it either has `base` on PATH or falls back to
  kb's own prose-execution contract.

Deep dive: [reference/entry-format.md](reference/entry-format.md) — what capture
composes as `--text`, and the corrections rule.
