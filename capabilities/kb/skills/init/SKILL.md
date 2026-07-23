---
name: init
description: "Creates a new base (knowledge base) — interview, BASE.yaml, scaffold, register, schedule. Use when the user wants a fresh base ('create a work base', 'kb init personal'), including during bootstrap when no base exists yet."
---

# init

**Invariant: init is not done until the schedules exist** (or their degraded mode is
materialized) — an unscheduled maintainer means an undrained inbox and an unenforced
contract.

## 1. The structure interview [A→H]

Ask once, design once — the user is never bothered about structure again (afterwards
the agent operates autonomously inside the frozen zone set; zone changes are
owner-approved BASE.yaml edits):

- **Name, path** (default `~/<name>-base`), **remote** (optional), **audience**
  (`private` default | `shared`), **sync** (`rebase-5min` needs a remote; adopted
  defaults stay manual).
- **Purpose** — one paragraph; it is the router's AND recall's rubric. Write it well.
- **Theme → zones and types.** An engineering base wants different zones/types than a
  family or self base. Start from the template defaults (entities/concepts/projects/
  profile) and adjust WITH the user; put the result in BASE.yaml (`zones:`, `types:`).
  Anything they say about *what belongs where* is routing gold — it becomes `purpose`
  text and `routing.keywords`.

## 2. Scaffold [D]

```
uv run <clone>/capabilities/kb/skills/kb/scripts/base.py \
  init <name> --path <path> --audience <a> --sync <s> --purpose "<p>" \
  [--remote <url>] [--default] --templates <clone>/capabilities/kb/skills/init/templates
```

The tool renders templates (BASE.yaml, AGENTS.md + Grants seed, index, log,
state.yaml, zone AGENTS files), git-inits with per-agent identity, registers in
`kb-registry.yaml`, logs `bootstrap`, commits. Then apply the interview's zone/type
adjustments to BASE.yaml + matching directories, and show the user the diff.

## 3. Schedules [D]

Create per the cheat-sheet (see the kb skill's `reference/wiring.md`): nightly-promote
+ weekly-lint as archiver agent jobs, sync as a **script-only exec job** — no LLM in
the loop. Single-owner rule applies. No cron host feature → materialize run-cards and
tell the user what to run when.

## 4. Verify [D]

`base lint` must run clean on the fresh tree. Report: tree, grants, registry entry,
schedules (or degraded modes).
