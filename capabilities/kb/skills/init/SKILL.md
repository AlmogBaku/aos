---
name: init
description: "Creates a new knowledge base: interviews the user for purpose, zones, types and curation, scaffolds the tree, registers it, and wires the maintenance schedules. Use when the user wants a fresh base ('create a work base', 'set me up a knowledge base', 'kb init personal'), including during bootstrap when none exists yet. Do NOT use when a knowledge tree already exists on disk — registering that in place is kb-adopt, and transforming another KB's content into a base is kb-import."
---

# init

**Init is not done until the schedules exist** (or their degraded run-cards do). An
unscheduled base means an undrained queue and an unenforced contract, which is worse than
no base at all.

## 1. The structure interview

Ask once, design once — the user is never bothered about structure again. Afterwards the
agent operates autonomously inside the frozen zone set, and a zone change is an
owner-approved `.kb/base.yml` edit.

- **Name, path** (default `~/<name>-base`), **remote** (optional), **audience**
  (`private` default, or `shared`), **sync** (`rebase-5min` needs a remote).
- **Purpose** — one paragraph. It is the rubric for both routing and recall. Write it well.
- **Theme → zones and types.** An engineering base wants different zones and types than a
  family or self base. Start from the template defaults and adjust *with* the user.
  Anything they say about what belongs where is routing gold: it becomes `purpose` prose
  and `routing.keywords`.
- **Curation** — on a shared base, who reviews what agents propose? `self` means each
  person curates their own captures (the default, and right for most teams); `designated`
  names one curator who drains everyone's. Private bases are always `self`.

## 2. Scaffold

```
kb init <name> --path <path> --audience <a> --sync <s> --purpose "<p>" \
  [--remote <url>] [--curation designated --curator <principal-id>] [--default]
```

The tool clones a template repo by default (read-only, unauthenticated, no fork) and drops
the clone's own history before rendering; `--template <url>` points at a different one, and
`--templates <local-dir>` skips the network entirely, which is also the automatic fallback
when a clone fails for any reason — announced, never silent, never blocking.

It renders the templates, git-inits, registers the base in `kb-registry.yaml`, writes
`<home>/.aos/kb-principal.yml` if it does not exist yet, and commits. It **does not** touch
the repo's git identity: the user's own identity authors every write and the acting agent is
recorded as committer, which is the attribution the weekly audit reads. Overwriting it with
a per-base agent identity would erase the one attribution git gives for free, and on a base
two people share it would make both of them the same author. If no git identity is
configured the tool says so and proceeds anyway — capture never blocks — and lint reports
the weak principal until onboarding fixes it.

Then apply the interview's zone and type adjustments to `.kb/base.yml` plus the matching
directories, and show the user the diff.

## 3. Schedules

Create them per the cheat-sheet (the `kb` skill's `reference/wiring.md` has the table):
`nightly-promote` and `weekly-maintain` as archiver agent jobs, `sync` as a script-only
exec job with no model in the loop. The single-owner rule applies. No cron on the harness →
materialize run-cards and tell the user what to run and when.

## 4. Verify

`kb lint` must run clean on the fresh tree. Report back: the tree, the grants, the registry
entry, and the schedules or their degraded modes.
