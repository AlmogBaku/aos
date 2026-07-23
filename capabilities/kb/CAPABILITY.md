---
id: kb
version: 0.2.0
tags: [infra]
summary: Multi-base knowledge infrastructure — registry, routing, the base engine (store · curation · state), the deterministic `base` tool, and one Archiver agent across all bases.
depends:
  host:
    cron: preferred
skills:
  - id: kb
    used_by: [main, archiver]
  - id: route
    used_by: [main]
  - id: recall
    used_by: [main]
  - id: init
    used_by: [main]
  - id: adopt
    used_by: [main]
schedules:
  - id: nightly-promote
    cron: "30 23 * * *"
    agent: archiver
    prompt_ref: agents/archiver/promote.md
    degraded: manual
  - id: weekly-lint
    cron: "0 7 * * 6"
    agent: archiver
    prompt_ref: agents/archiver/lint.md
    degraded: manual
  - id: sync
    cron: "*/5 * * * *"
    exec: skills/kb/scripts/base.py sync --all
    degraded: manual
kb:
  zones:
    - path: "raw/"
      owner_agent: archiver
    - path: "entities/"
      owner_agent: archiver
    - path: "concepts/"
      owner_agent: archiver
    - path: "projects/"
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

# kb — installer's briefing

*(This document is consumed at install and not used afterwards. The runtime face of
the capability is the `kb` entry skill.)*

## What this is

The root infrastructure capability: every base (KB instance, `base == repo`) a user
has, plus the machinery around them — registry, routing, grants, the three-pillar
engine (store: raw + current-truth wiki pages; curation: capture → skeptical
promotion → lint; state: one capped attention window per base), the deterministic
`base` tool (bundled in the entry skill's `scripts/`), and one Archiver agent that
serves all bases. Other capabilities declare abstract `kb.writes` intents; the route
skill resolves them.

## What you materialize, and why

1. **Skills** per `used_by`: the `kb` entry skill goes to the front agent AND the
   archiver — it carries the map and the tool, so everyone who touches bases has both.
   `route`/`recall`/`init`/`adopt` are front-agent judgment skills. Skill directories
   are copied whole (reference/, scripts/, templates/ travel with them).
2. **The archiver agent** (`agents/archiver.agent.yaml`): create per the cheat-sheet.
   One archiver for all bases — cross-base re-routing is its point. It must have no
   messaging tools (enforce via harness tool configuration, not instructions). Its
   prompt bodies live in `agents/archiver/`.
3. **Schedules — in the same session as any base, never deferred.** `nightly-promote`
   (23:30, after gtd-capture's 23:00 drain) and `weekly-lint` are agent jobs on the
   archiver. **`sync` is an exec job**: wire the harness cron to run
   `uv run <clone>/capabilities/kb/skills/kb/scripts/base.py sync --all` directly —
   deterministic-only, no LLM wakes up; optionally compose the harness's notifier
   around it (`… || notify`). All degrade to `manual` run-cards without cron.
4. **Zones**: the `kb.zones` above are the archiver's maintenance surface in each
   base — grant rows appended to that base's `AGENTS.md` at install (user-approved
   diff), revoked at removal. The front agent additionally gets `raw/captures/**`
   (route-into) and `state.yaml` + `profile/**` (write) rows — seeded by the init
   templates.
5. **Onboarding** asks which bases exist; `init`/`adopt` then write the user-owned
   `kb-registry.yaml` (overlay family — never committed upstream). The init interview
   designs each base's zones/types once (theme-driven), written into its BASE.yaml.

## Contracts to preserve

- The tool is the canonical executor of deterministic operations; it never calls an
  LLM; prose execution is the degraded mode (kb skill → reference/wiring.md).
- Shared bases never accept LLM-routed or unreviewed agent writes (RFC-006's
  uncontested core; route skill).
- `BASE.yaml layout: 1` — tools refuse loudly on mismatch; never path-guess.

## Contested core — RFC-006

`skills/route/SKILL.md` implements §4.2 as specced. RFC-006 owns the confidence bar,
rule tie-breaking, and drain-approval batching.
