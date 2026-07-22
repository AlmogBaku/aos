---
id: gtd-capture
version: 0.1.1
tags: [usecase]
summary: Voice/text → next-action → KB write → reminder.
depends:
  capabilities: [kb, onboarding]
  host:
    cron: preferred
    messaging.inbound: required
schedules:
  - id: nightly-drain
    cron: "0 23 * * *"
    agent: drainer
    prompt_ref: skills/drain/drain-prompt.md
    degraded: manual
skills:
  - id: capture
    used_by: [main]
  - id: drain
    used_by: [drainer]
  - id: format-entry
    used_by: [drainer, main]
kb:
  writes: [inbox]
  zones:
    - path: ops/inbox.md
      owner_agent: drainer
---

# gtd-capture

Capture is dumb and fast; the drain does the thinking. A thought on any bound channel →
one line in the routed KB inbox in under five seconds → the nightly drain turns it into
next-actions and reminders.

## Install narrative

1. **Capture path**: the `capture` skill → front agent only; it composes with kb's
   `route` skill.
2. **Drainer agent** (`agents/drainer.agent.yaml`): the `drain` skill is
   `used_by: [drainer]` — the front agent never loads it.
3. **Schedule**: default 23:00; the user's `drain_hour` answer overrides the cron at
   materialization. Runs before kb's 23:30 `nightly-promote`: drain triages and marks
   `#triaged`, promote files into `raw/` and empties the inbox. Drain never deletes
   lines.
4. **Zone**: register `ops/inbox.md` in the target KB (template in `kb/zones/`); grant
   the drainer `write` and the capture path `route-into`.
5. **Reminders**: outbound messaging to the `reminder_target` answer; without
   `messaging.outbound`, degrade to a line in the drain report.

Transform: fill `{{mod: capture_preferences}}` in the capture skill; use `drain_hour`,
`inbox_kb`, `action_format` answers for the schedule and drain behavior.
