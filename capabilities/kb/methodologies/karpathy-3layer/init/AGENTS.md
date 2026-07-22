# AGENTS — {{kb_name}} root contract

> Read this BEFORE any non-trivial write. This is the contract every agent honors.

## What this repo is

A shared multi-agent knowledge substrate — not any one agent's filesystem. Every registered
agent reads everything; only a zone's granted maintainer writes to it. Three layers:

1. **`raw/`** — immutable sources, append-only, sha256-deduplicated, never edited in place.
   A wrong fact gets a Layer-2 correction page linking back, never an edit here.
2. **The semantic layer** — `entities/ concepts/ comparisons/ queries/ projects/ domains/`:
   synthesized pages with `[[wikilinks]]` and schema frontmatter. Editable, grown by the
   archiver, corrected by anyone with a grant.
3. **`state/`** — high-churn current truth ("what's going on now"). Rewritten, not
   appended. Never an archive.

Operational scaffolding: `ops/` (live capture + task workflow), `drafts/` (WIP not yet
promoted), `_ops/` (KB metadata: lint reports, review queues), `_archive/` (let-it-rot
graveyard — nothing is deleted, it rots here).

## Grants

The authorization table (one ACL for routing, writing, and the permission gate — same
vocabulary everywhere). **Cross-zone writes require a row here first.** Default posture is
deny: no row, no verb; unregistered agents match nothing, not even `*`.

| subject | object | verbs | grantor | granted | via | notes |
|---|---|---|---|---|---|---|
| user | `**` | read write grant | — | {{today}} | — | root of authority |
| agent:archiver | `raw/**` | write route-into | user | {{today}} | kb@{{version}} | append-only; sha256 dedup |
| agent:archiver | `entities/** concepts/** comparisons/** queries/**` | write | user | {{today}} | kb@{{version}} | Layer-2 synthesis |
| agent:archiver | `_ops/** _archive/** index.md log.md` | write | user | {{today}} | kb@{{version}} | log is append-only |
| agent:main | `ops/**` | write route-into | user | {{today}} | kb@{{version}} | the live capture path |
| agent:main | `state/**` | write | user | {{today}} | kb@{{version}} | rewrite whole files; budgets in state/AGENTS.md |
| `*` | `**` | read | user | {{today}} | kb@{{version}} | registered agents read everything |
| `*` | `drafts/**` | write | user | {{today}} | kb@{{version}} | WIP; archiver sweeps weekly |

Rules the table can't carry:

- **Registration is the boundary.** An agent appears in this KB's life by getting a row
  (or matching `*` as a *registered* agent of this user's harness). A write by anything
  else is refused; refusal preserves data (`refuse` log line + `_ops/needs-review.md`
  block; the payload stays with the caller).
- The weekly lint audits `git log` authorship against this table (per-agent git identity —
  `kb init` configures it). A write with no matching row is a finding, every time.
- Adding, changing, or revoking rows: `user` only in v0.1. Install-time rows carry `via`
  so removal is mechanical.

## Required reading order (any session, any agent)

1. This file. 2. `SCHEMA.md`. 3. `index.md` (the map of content). 4. `log.md` — last 30
lines. 5. *Front agent only:* `state/STATE.md`, then the state stack. 6. **Archiver: stop
after step 4.** The librarian never loads `state/` — context isolation is what keeps its
voice mechanical and its judgment free of the user's business.

## Write rules

- **sha256 dedup** on every `raw/` ingest. Same hash, no new file.
- **`[[wikilinks]]`** for every entity reference. Unresolved mention → append to
  `_ops/needs-entity-queue.md`; never auto-create a stub.
- **Frontmatter** per `SCHEMA.md` on every Layer-2 page; `state/` files carry the minimal
  Layer-3 header (`updated:`, `maintainer:`).
- **One writer per file per minute.** Sync is git rebase every 5 minutes, atomic per file;
  concurrent writes to one file lose. Design around it — zones exist so you never share a
  file with another writer.
- **Append-only `log.md`**, canonical line format (see SCHEMA.md §log). One line per
  synthesis mutation. Never edit existing lines. Git history covers what the log doesn't.
- **Page-or-inline**: a new page only if the concept is referenced from ≥2 places or the
  user asked; otherwise inline in the parent.
- **No `.backup.*` files, ever** — git history is the archive. (Lint flags them.)
- Status narratives, heartbeats, checkpoints: **not KB content** — they go to your own
  workspace outside this repo (lint-flagged as pollution here).

## Sync

{{mod: sync_mode}} — default: auto-commit + `git pull --rebase` + push every 5 minutes
(the methodology's `kb-sync` schedule). Conflicts are never auto-resolved: the sync aborts
the rebase, logs `sync-conflict`, and surfaces to the user's next brief.

## When in doubt

Don't write — read, then surface the question (`_ops/needs-review.md`, with evidence and
a stated default).
