---
x-aos-origin: kb@0.3.0
name: kb
description: "The knowledge-base system's front door — bases, capture, state, recall. Use when working with the user's knowledge bases and no narrower kb skill applies: understanding how bases work, orienting into 'where things stand', filing or finding knowledge, checking base health, running maintenance, or any mention of 'base', 'KB', 'knowledge base', 'my notes', or 'state of mind'."
---

# kb — the base system, in one page

**Invariant: files are the database.** Every base is a git repo of markdown + two YAML
files; every index is a rebuildable derivative; the `base` tool never calls an LLM —
judgment is yours, mechanics are its.

## The mental model (three pillars)

- **Store** — `raw/` (sources, immutable after triage) + **wiki pages** (entities,
  concepts, projects — **current truth only**: facts replaced in place, history is git,
  `## Timeline` sections are event ledgers).
- **Curation** — `base capture` (instant, deduped) → nightly Archiver promotion
  (skeptical: most captures never become pages) → weekly lint → your review queue.
- **State** — `state.yaml` per base: the capped attention window ("where is my head"),
  one-liners pointing into pages. Read it to orient; never treat it as knowledge.

## Where things live

- `kb-registry.yaml` (clone root, user-owned) — every base: path, audience, purpose,
  routing hints, which is default.
- Each base: `BASE.yaml` (machine config — the tool enforces it), `AGENTS.md`
  (contract + Grants table — read before writing), `index.md` (the map; descriptions
  are the ToC), `log.md` (audit), `state.yaml`, zones per BASE.yaml.

## Cold start ("where do things stand?")

Read `state.yaml` of every base you're registered in, **private bases first**. That
composition is the user's head. Bump items you materially use (only if you are the
base's state writer): `base state bump --note <substring>`.

## The tool

`base --help` (installed at capability install: `uv tool install --from <clone>/capabilities/kb/tool aos-base`; one-off: `uvx --from <clone>/capabilities/kb/tool base`) — deterministic
verbs; every write logs itself. Key ones: `capture` (never hand-write into raw/),
`inbox` (pending view), `state add|bump|drop|check`, `search` (check before creating
ANY page — `EXISTS` means stop), `links`, `lint`, `grants check`, `index rebuild`,
`sync`, `verify` (user confirmed a page → flips `verified: true`), `import survey` (inventory + shape detection of a foreign tree — the import skill's mechanical first step). Degraded mode (no
uv/python): perform the same contracts by hand per each base's AGENTS.md — slower,
same rules.

## Which skill for which job

| Job | Skill |
|---|---|
| File/capture something, destination unclear | `route` |
| Answer "what do I know about X?" | `recall` |
| Create a new base | `init` |
| Register an existing tree | `adopt` |
| Migrate/import an existing KB's content | `import` (interactive — never autonomous) |
| Contract details (grants, page schema, lifecycle) | `reference/` here |

## Authority

- May freely: read anything granted; capture; bump state; run `search`/`links`/`lint`.
- Report-only: lint findings, sync conflicts (they land in `_ops/needs-review.md` —
  the user drains that queue, never you).
- Ask first: creating pages in a **shared** base (review queue always), zone/type
  changes (BASE.yaml is owner-approved), anything `profile/`, flipping `verified`.

Deep dives, one level down: [reference/lifecycle.md](reference/lifecycle.md) (page
schema, current-truth doctrine, triage, verified/origin) ·
[reference/grants.md](reference/grants.md) (the Grants table: check, register, revoke)
· [reference/wiring.md](reference/wiring.md) (schedules, cron wiring, degraded modes).
