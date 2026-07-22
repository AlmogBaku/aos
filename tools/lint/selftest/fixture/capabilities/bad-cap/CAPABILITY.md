---
id: wrong-id
version: not-semver
tags: [infra, nonsense]
provides: speculative-field
depends:
  capabilities: [does-not-exist]
  host:
    teleportation: required
    cron: sometimes
schedules:
  - id: dup
    cron: "0 23 * * *"
    agent: nobody
    prompt_ref: missing/prompt.md
    degraded: explode
    retries: 3
  - id: dup
    cron: "whenever"
    agent: main
    prompt_ref: missing/prompt.md
    degraded: manual
skills:
  - id: capture
    used_by: [phantom]
    extra_key: true
  - id: missing-skill
    used_by: [main]
  - id: BadName
kb:
  writes: [notes]
  zones:
    - path: ops/inbox.md
      owner_agent: nobody
      extra: true
---

A deliberately broken capability. Every violation here must be caught by
exactly the check named in ../../../expected-codes (the selftest contract).
