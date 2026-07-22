---
id: kb
version: 0.1.0
tags: [infra]
summary: Multi-KB infrastructure — registry, routing, authorization, and one shipped methodology (karpathy-3layer) with its Archiver agent.
depends:
  host:
    scheduler: preferred
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

The root infrastructure capability: every other capability that touches knowledge declares
abstract `kb.writes` intents and lets this capability's router resolve them. It owns the
user's KB registry (`kb-registry.yaml`), the routing and authorization skills, and ships
exactly one methodology — `karpathy-3layer` — behind the pluggable methodology seam
(ARCHITECTURE §4.4).

## Install narrative

1. **Skills.** `route`, `init`, `adopt` materialize to the front agent; `authz-check` to
   both the front agent and the archiver (it is the shared grant-table lookup both sides
   use — one ACL, not two, §4.3).
2. **The archiver agent** (`agents/archiver.agent.yaml`) is created per the cheat-sheet's
   agent mapping. Its persona is deliberately isolated: it never loads the user's `state/`
   context, never messages the user directly, and its messaging tools are excluded at the
   harness level, not by instruction (see the agent spec).
3. **Schedules** belong to the archiver and are created **in the same session as any KB
   tree**. `nightly-promote` runs at 23:30 — deliberately *after* gtd-capture's 23:00
   drain, so GTD triage (actions, reminders) happens before the librarian files the same
   entries into `raw/` — a fully-specified-but-never-scheduled maintainer is the single biggest failure
   mode observed in the live setup this was extracted from. `kb-sync` materializes as a
   no-agent script job where the harness supports it (the methodology ships the script);
   `nightly-promote` and `weekly-lint` are agent jobs with their prompts in the methodology
   package. All three degrade to `manual`: an invocable run-card materialized as a skill.
4. **Zones.** The `kb.zones` above are the archiver's maintenance surface *within each KB
   that adopts the shipped methodology* — appended to that KB's `AGENTS.md` `## Grants`
   table at install (drafted by the installer, approved by the user) and revoked at
   removal.
5. **Onboarding** (`ONBOARDING.md`) asks which KBs exist; the `init`/`adopt` skills then
   write the user-owned `kb-registry.yaml`. The registry is overlay family — never shipped,
   never committed upstream (§3.1).

## Contested core — deferred to RFC-006

The routing behavior in `skills/route/SKILL.md` implements ARCHITECTURE §4.2 as specced:
rules first, one confidence-gated LLM call among **private** KBs only, uncertain → default
inbox. The confidence bar value, tie-breaking precedence, and drain-approval batching are
**RFC-006 territory** — the skill marks them and the replay evidence decides. Shared KBs
never accept LLM-routed writes; that safety property is not contested and is enforced by a
candidate-set filter, not a threshold.
