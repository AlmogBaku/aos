---
id: uses-cap
version: 0.1.0
tags: [usecase]
summary: Plants a foreign skill reached by its own agent without a uses grant, and malformed grants.
depends:
  capabilities: [name-cap, prefix-cap]
schedules:
  - id: nightly
    cron: "0 3 * * *"
    agent: scribe
    prompt_ref: schedules/nightly.md
    degraded: skip
skills:
  - id: uses-cap
    used_by: [scribe]
  - id: shared
    used_by: [main, scribe]
  - id: covered
    used_by: [scribe]
uses:
  - {capability: prefix-cap, skill: tidy, agents: [scribe]}
  - {capability: prefix-cap, skill: tidy, agents: [scribe]}
  - {capability: name-cap, skill: nosuch, agents: [scribe]}
  - {capability: half-cap, skill: half-cap, agents: [scribe]}
  - {capability: name-cap, skill: capture, agents: [ghost], why: planted}
---

Plants uses/missing twice (a skill and a schedule prompt the `scribe` agent loads), a dangling
slot in that prompt, and one of each malformed grant. Two references must stay silent: one in
a skill main also loads, one the first grant covers.
