---
questions:
  - id: capture_channels
    prompt: Where do you fire off commitments — which channels should this listen on?
    type: list
    required: true
  - id: reminder_target
    prompt: Where should reminders and the nightly report reach you?
    type: string
    required: true
  - id: calendar_target
    prompt: Which calendar should time blocks be written to?
    type: string
  - id: working_windows
    prompt: When are you willing to have work blocked — beyond the working hours you already gave?
    type: string
  - id: estimate_granularity
    prompt: How precise should time estimates be (15 minutes, half hours, hours)?
    type: enum
  - id: steward_hour
    prompt: What time should the nightly backlog pass run?
    type: string
  - id: followup_cadence
    prompt: How long should something sit with someone else before you are nudged about it?
    type: string
  - id: retention_days
    prompt: How long should completed commitments stay before they are deleted?
    type: number
  - id: slip_threshold
    prompt: After how many reschedules should a commitment be questioned rather than moved again?
    type: number
  - id: action_format
    prompt: How do you like commitments phrased back to you?
    type: string
---

# work-tracker interview

Runs at install, after the kb and global interviews — **their answers are context, so do not
re-ask**. The global `MOD.md` already has the timezone, working hours, sacred time and red
lines; this interview asks only what work-tracker itself needs.

There is deliberately **no question about which base** commitments go in. There is exactly one,
it must be `audience: private`, and asking would offer a choice that does not exist.

1. **`capture_channels`** — *"Where do you tend to say 'I need to…'? WhatsApp to your agent,
   voice notes, the chat here?"* Channel names as the harness knows them; the cheat-sheet's
   channel binding is built from these.
2. **`reminder_target`** — one delivery target (`whatsapp`, `chat`, a channel id). If the
   harness has no outbound messaging, say so plainly: reminders and the nightly report appear
   when they next talk to the agent instead.
3. **`calendar_target`** — which calendar, if they have more than one. Worth asking *"work or
   personal?"* here even though capture never asks it: a block on the wrong calendar is visible
   to the wrong people. No calendar available → say so now rather than at the first
   *"find me two hours"*: commitments, deadlines and the nightly pass all still work, and
   nothing gets blocked.
4. **`working_windows`** — the global answer covers *"9:00–18:00 weekdays"*. This is for the
   nuance on top: *"nothing before 10:00"*, *"Friday afternoons are for admin"*, *"never
   two long blocks back to back"*. Anything idiosyncratic goes in the body under
   `## Scheduling preferences`, which is what prose is for.
5. **`estimate_granularity`** — `15m` · `30m` · `1h`. This is about how estimates are *shown*,
   not how they are stored. Inventing precision they did not ask for (`37m`) reads as noise.
6. **`steward_hour`** — default 23:00, `HH:MM`. The materialized cron uses it. Unlike the old
   design there is **no ordering constraint** against kb's own nightly job, so any hour is
   fine; if they pick something after midnight, confirm which day's backlog that means.
7. **`followup_cadence`** — default 14 days. How long a `waiting` commitment sits before the
   steward raises it. Someone who chases people weekly and someone who lets things breathe
   want very different numbers here.
8. **`retention_days`** — default 90. How long a completed commitment survives before
   `kb prune` deletes it. Reassure them what this does *not* delete: knowledge went to the
   knowledge base when the commitment completed, so this only removes the bookkeeping.
9. **`slip_threshold`** — default 3. *"One slip is life; three usually means the commitment
   itself is wrong."* Below this the steward reschedules silently; at it, it asks whether the
   thing still matters.
10. **`action_format`** — show two and let them react: *"verb-first: 'Email Sam the deck'"* vs
    *"outcome-first: 'Sam has the deck'"*. Their phrasing preference, including anything
    idiosyncratic, is exactly what the body prose is for.

Confirmation style (*"just a ✅"*, a specific emoji, no confirmation at all) is nuance → body,
under `## Capture preferences`.
