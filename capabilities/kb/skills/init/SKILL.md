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

Then apply the interview's zone and type adjustments with `kb config set` (for example
`kb config set 'zones.decisions={kind: wiki}'`), which commits each change itself, and create
the matching directories. Show the user the diff. A hand-edit of `.kb/base.yml` also works
but leaves the tree uncommitted, which lint reports as a finding — so follow one with
`kb commit --verb config --path .kb/base.yml --summary "<what changed>"`.

## 3. Schedules

Three jobs, and init is not finished until all three exist. The harness cheat-sheet gives the
exact cron syntax for this harness; what does not vary is *what* to schedule:

| id | when | runs | as |
|---|---|---|---|
| `nightly-promote` | `30 23 * * *` | the archiver agent, prompt `agents/archiver/promote.md` | agent job |
| `weekly-maintain` | `0 7 * * 6` | the archiver agent, prompt `agents/archiver/lint.md` | agent job |
| `sync` | `*/5 * * * *` | `kb sync --all` | **exec job — no model wakes up** |

Three things silently break if you skip them, and each fails quietly rather than loudly:

- **`AOS_AGENT=agent:archiver` in both archiver jobs.** It defaults to `agent:main`, which
  holds no write grant on `entities/** concepts/** projects/** index.md` — so a job that
  looks like it worked commits every promotion as the wrong subject, and the next weekly
  lint reports each one as a grants-audit **critical**.
- **`AOS_REGISTRY=<home>/personal/kb-registry.yaml` in the sync wrapper** (or pass
  `--registry`), because a bare `kb sync` with no resolvable registry exits **0** having
  synced nothing.
- **The single-owner rule**: each of these runs in exactly one harness, so check none of
  them already exists before creating it.

**No cron on this harness?** Then all three degrade to `manual` run-cards: write down the
command and the trigger for each ("run `kb sync --all` when you finish a session"; "ask the
archiver to promote overnight"), and tell the user, because nothing will run them otherwise.

## 4. Verify

`kb lint` must report **zero Critical and zero Findings** on the fresh tree (Info lines are
fine — they are observations, not defects). Report back: the tree, the grants, the registry
entry, and the schedules or their degraded modes.
