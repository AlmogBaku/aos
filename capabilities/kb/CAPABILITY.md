---
id: kb
version: 0.1.1
tags: [infra]
summary: Multi-KB infrastructure — registry, routing, authorization, and one shipped methodology (karpathy-3layer) with its Archiver agent.
depends:
  host:
    cron: preferred
skills:
  - id: route
    used_by: [main]
  - id: authz-check
    used_by: [main, archiver]
  - id: init
    used_by: [main]
  - id: adopt
    used_by: [main]
schedules:
  - id: nightly-promote
    cron: "30 23 * * *"
    agent: archiver
    prompt_ref: methodologies/karpathy-3layer/archiver/promote.md
    degraded: manual
  - id: weekly-lint
    cron: "0 7 * * 6"
    agent: archiver
    prompt_ref: methodologies/karpathy-3layer/archiver/lint.md
    degraded: manual
  - id: kb-sync
    cron: "*/5 * * * *"
    agent: archiver
    prompt_ref: methodologies/karpathy-3layer/archiver/sync.md
    degraded: manual
kb:
  zones:
    - path: "raw/"
      owner_agent: archiver
    - path: "entities/"
      owner_agent: archiver
    - path: "concepts/"
      owner_agent: archiver
    - path: "_ops/"
      owner_agent: archiver
    - path: "_archive/"
      owner_agent: archiver
    - path: "index.md"
      owner_agent: archiver
    - path: "log.md"
      owner_agent: archiver
---

# kb

The root infrastructure capability. Other capabilities declare abstract `kb.writes`
intents; this capability's router resolves them. Ships one methodology,
`karpathy-3layer`, behind the pluggable methodology seam (ARCHITECTURE §4.4).

## Install narrative

1. **Skills**: `route`, `init`, `adopt` → front agent; `authz-check` → front agent AND
   archiver (one shared ACL, §4.3).
2. **Archiver agent** (`agents/archiver.agent.yaml`): create per the cheat-sheet. It
   never loads the user's `state/` context and must have no messaging tools — enforce
   via harness tool configuration, not instructions.
3. **Schedules** belong to the archiver and are created **in the same session as any KB
   tree** — never deferred. `nightly-promote` runs at 23:30, after gtd-capture's 23:00
   drain (drain marks entries, promote files and removes them). `kb-sync` materializes
   as a no-agent script job where supported. All degrade to `manual` (invocable
   run-card skill).
4. **Zones**: the `kb.zones` above are the archiver's maintenance surface in each KB
   using the shipped methodology — grant rows appended to that KB's `AGENTS.md` at
   install (user-approved), revoked at removal.
5. **Onboarding** asks which KBs exist; `init`/`adopt` then write the user-owned
   `kb-registry.yaml` (overlay family — never committed upstream).

## Contested core — RFC-006

`skills/route/SKILL.md` implements §4.2 as specced. RFC-006 owns the confidence bar,
rule tie-breaking, and drain-approval batching. Not contested: shared KBs never accept
LLM-routed writes (candidate-set filter, not a threshold).
