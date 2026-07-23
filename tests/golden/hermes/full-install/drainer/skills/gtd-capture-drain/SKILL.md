---
name: drain
description: The nightly GTD triage over the inbox — turns captures into next-actions, reminders, and project updates. Use when the nightly-drain schedule fires or the user asks to drain the inbox now.
x-aos-origin: gtd-capture@0.1.1
---

# drain

You run before the archiver's promote pass. **Never delete inbox lines** — you read,
decide, act, and mark; promote removes.

For each untriaged entry (no `#triaged` tag), oldest first:

1. `#correction` entries first: apply to whatever they supersede.
2. Actionable, < 2 min of agent work → do it now, note the outcome.
3. Actionable task → write/update the next-action per the user's `action_format` answer:
   the owning `projects/` page's `next_action` frontmatter, or the tasks list for
   standalone items. Deadline phrasing → set a reminder.
4. Not actionable (reference, idea, fact) → leave it; promote files knowledge.
5. Reminders: deliver via outbound messaging to `reminder_target` at the implied time.
   No outbound messaging → list in the drain report instead.
6. Mark: append `#triaged` to the entry's tag group (per `format-entry` — tag group only,
   touch nothing else on the line).
7. `#kb-routing-uncertain` entries: obvious private-KB home → note the re-route for the
   archiver. Shared-KB home → propose in `_ops/needs-review.md`, never auto.

Constraints from the global MOD.md: a reminder never fires inside a sacred-time window —
move it to the window's end. Red lines apply.

Close with the drain report (actions created, reminders set, two-minute items done),
delivered per the schedule. Nothing untriaged → output exactly `DRAIN: inbox clean.` and
deliver nothing.
