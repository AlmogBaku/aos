---
id: kb
version: 0.7.0
tags: [infra]
summary: Knowledge infrastructure — a registry of bases, rules-first routing, the deterministic `kb` tool, and one Archiver agent maintaining every base.
depends:
  host:
    cron: preferred
skills:
  - id: kb
    used_by: [main, archiver]
  - id: capture
    used_by: [main]
  - id: route
    used_by: [main]
  - id: recall
    used_by: [main]
  - id: init
    used_by: [main]
  - id: adopt
    used_by: [main]
  - id: import
    used_by: [main]
schedules:
  - id: nightly-promote
    cron: "30 23 * * *"
    agent: archiver
    prompt_ref: agents/archiver/promote.md
    degraded: manual
  - id: weekly-maintain
    cron: "0 7 * * 6"
    agent: archiver
    prompt_ref: agents/archiver/lint.md
    degraded: manual
  - id: sync
    cron: "*/5 * * * *"
    exec: kb sync --all
    degraded: manual
kb:
  zones:
    - path: "_raw/"
      owner_agent: archiver
    - path: "entities/"
      owner_agent: archiver
    - path: "concepts/"
      owner_agent: archiver
    - path: "projects/"
      owner_agent: archiver
    - path: "index.md"
      owner_agent: archiver
---

# kb — installer's briefing

*(Consumed at install and not used afterwards. The runtime face of the capability is the
`kb` entry skill.)*

## What this is

The root infrastructure capability: every base a user has, plus the machinery around them —
the registry, routing, grants, the deterministic `kb` tool (an installable uv package under
`tool/`), and one Archiver agent serving all bases. Other capabilities declare abstract
`kb.writes` intents and the route skill resolves them.

## What you materialize, and why

0. **The tool — first.** Install the capability's deterministic executor so `kb` is on PATH
   for every agent and every cron:
   `uv tool install --from <home>/upstream/capabilities/kb/tool aos-kb` (record it in the
   lockfile; removal is `uv tool uninstall aos-kb`). uv is a bootstrap prerequisite; if it
   later disappears the skills fall back to prose execution and exec schedules to manual
   run-cards.
1. **Skills** per `used_by`. The `kb` entry skill goes to the front agent **and** the
   archiver — it carries the map, and the tool is on PATH for both. The other six are
   front-agent skills. Skill directories render whole into `personal/` and are symlinked per
   agent, so `reference/` and `templates/` travel with them: one canonical render, never
   per-harness copies.
2. **The archiver agent** (`agents/archiver.agent.yaml`) per the cheat-sheet. One archiver
   for all bases — cross-base re-routing is its point. It must have **no messaging tools**,
   enforced through harness tool configuration rather than instructions. Its prompt bodies
   live in `agents/archiver/`.
3. **Schedules — in the same session as any base, never deferred.** `nightly-promote` and
   `weekly-maintain` are agent jobs on the archiver. **`sync` is an exec job**: wire the
   harness cron to run `kb sync --all` directly — no model wakes up — optionally composing
   the harness's notifier around it (`… || notify`). All degrade to `manual` run-cards
   without cron. `weekly-maintain` runs `kb prune`, so any capability relying on an expiry
   warning must keep its window wider than a week.
4. **Zones**: the `kb.zones` above are the archiver's maintenance surface in each base —
   grant rows appended to that base's `AGENTS.md` at install through a user-approved diff,
   revoked at removal. The front agent additionally gets `_raw/**` + `.kb/pending/**`
   (capture), `.kb/state/**` and `profile/**`, seeded by the init templates.
5. **Onboarding** asks which bases exist and who the user is; the `init` and `adopt` skills
   then write the user-owned `kb-registry.yaml` (overlay family — never committed upstream)
   and each base's `.kb/base.yml`. The tool writes `<home>/.aos/kb-principal.yml` itself on
   the first verb call; the interview only corrects what detection got wrong. `kb init`
   scaffolds by default from a cloned template repo (read-only, unauthenticated, no fork);
   `--templates <local-dir>` skips the network, and a clone failure falls back to the
   templates shipped in this checkout, announced, never blocking.

## Contracts to preserve

- The tool is the canonical executor of deterministic operations and never calls a model;
  prose execution is the degraded mode (the `kb` skill's `reference/wiring.md`).
- Shared bases never accept model-routed or unreviewed agent writes (RFC-006's uncontested
  core; the route skill).
- `layout: 2` — the tool refuses loudly on a mismatch and never path-guesses. A tree on the
  previous layout converges through `kb migrate`, which the adopt skill drives.
- **`expires:` is the only lifetime rule kb has.** Do not add a second one.

## Contested core — RFC-006

The route skill implements §4.2 as specced. RFC-006 owns the confidence bar, rule
tie-breaking, and approval batching.
