---
id: gtd-capture
version: 0.1.0
tags: [usecase]
summary: Voice/text → next-action → KB write → reminder.
depends:
  capabilities: [kb, onboarding]
  host:
    scheduler: preferred
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

The first vertical: capture is dumb and fast, the drain does the thinking. A thought
arrives on any bound channel → one line lands in the routed KB's inbox in under five
seconds → the nightly drain turns it into next-actions, reminders, and filed knowledge.

## Install narrative

1. **Capture path.** The `capture` skill goes to the front agent only. It composes with
   kb's `route` skill: an incoming capture is routed (explicit tag → channel/keyword rule
   → confidence-gated LLM among private KBs → default inbox) and appended in the
   one-line entry format. No classification, no questions, no lookups at capture time —
   the latency budget is the whole point.
2. **Drainer agent** (`agents/drainer.agent.yaml`): the GTD triage clerk. Its `drain`
   skill is scoped `used_by: [drainer]` — the front agent never loads it.
3. **Schedule.** `nightly-drain` defaults to 23:00; the user's `drain_hour` answer
   overrides the cron at materialization. It deliberately runs *before* kb's 23:30
   `nightly-promote`: drain triages entries into actions and reminders and marks them
   `#triaged`; the archiver then files the same entries into `raw/` and empties the
   inbox. Two agents, one inbox, strict order — drain never deletes lines, promote does.
4. **Zone.** `ops/inbox.md` is registered in the target KB (template in `kb/zones/`);
   the grant row gives the drainer `write` and the front agent's capture path
   `route-into` (kb's install already granted `agent:main` the ops/ write).
5. **Reminders** deliver via the harness's outbound messaging to the user's
   `reminder_target` answer; without `messaging.outbound` they degrade to a line in the
   drain report.

The transform weaves MOD.md nuances at the `{{mod: capture_preferences}}` slot in the
capture skill and uses `drain_hour`, `inbox_kb`, and `action_format` answers to
materialize the schedule and drain behavior.
