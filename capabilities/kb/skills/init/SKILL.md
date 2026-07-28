---
name: init
description: "Creates a new base (knowledge base) — interview, scaffold, register, schedule. Use when the user wants a fresh base ('create a work base', 'kb init personal'), including during bootstrap when no base exists yet."
---

# init

**Invariant: init is not done until the schedules exist** (or their degraded mode is
materialized) — an unscheduled maintainer means an undrained inbox and an unenforced
contract.

## 1. The structure interview [A→H]

Ask once, design once — the user is never bothered about structure again (afterwards
the agent operates autonomously inside the frozen zone set; zone changes are
owner-approved `.kb/base.yml` edits):

- **Name, path** (default `~/<name>-base`), **remote** (optional), **audience**
  (`private` default | `shared`), **sync** (`rebase-5min` needs a remote; adopted
  defaults stay manual).
- **Purpose** — one paragraph; it is the router's AND recall's rubric. Write it well.
- **Theme → zones and types.** An engineering base wants different zones/types than a
  family or self base. Start from the template defaults (entities/concepts/projects/
  profile) and adjust WITH the user; put the result in `.kb/base.yml` (`zones:`,
  `types:`). Anything they say about *what belongs where* is routing gold — it becomes
  `purpose` text and `routing.keywords`.

## 2. Scaffold [D]

```
kb init <name> --path <path> --audience <a> --sync <s> --purpose "<p>" \
  [--remote <url>] [--default]
```

By default the tool `git clone`s a template repo (read-only, unauthenticated, no
fork — just the templates, hosted for discoverability) and drops the clone's own
`.git` history before rendering; `--template <url>` points at a different one. Pass
`--templates <local-dir>` to skip the network step entirely and render straight from a
local directory instead (defaults to
`<home>/upstream/capabilities/kb/skills/init/templates` when the clone fails for any
reason — no network, bad URL, git not configured for the host — and this is announced,
never silent, never blocking).

The tool renders templates (`.kb/base.yml`, `AGENTS.md` + Grants seed, `index.md`,
per-principal state shard, zone `AGENTS.md` files), git-inits with the user's own git
identity, registers in `kb-registry.yaml`, commits `bootstrap`. Then apply the
interview's zone/type adjustments to `.kb/base.yml` + matching directories, and show
the user the diff.

## 3. Schedules [D]

Create per the cheat-sheet (see the kb skill's `reference/wiring.md`): nightly-promote
+ weekly-lint as archiver agent jobs, sync as a **script-only exec job** — no LLM in
the loop. Single-owner rule applies. No cron host feature → materialize run-cards and
tell the user what to run when.

## 4. Verify [D]

`kb lint` must run clean on the fresh tree. Report: tree, grants, registry entry,
schedules (or degraded modes).
