# Grants reference — the one ACL

## Contents
- The table
- Checking
- Registering (install) and revoking (removal)
- Enforcement, honestly

## The table

The first markdown table under `## Grants` in each base's `AGENTS.md` — one ACL for
routing, writing, and the future permission gate. Columns (do not rename — parsed):
`subject | object | verbs | grantor | granted | via | notes`.

- `subject`: `user` · `agent:<name>` · `capability:<id>` · `*` (any *registered*
  subject — unregistered agents match nothing, not even `*`).
- `object`: git-style glob(s), space-separated, relative to the base root
  (`**` crosses `/`, `*` doesn't).
- `verbs`: subset of `read write route-into grant`. Default posture is **deny** — no
  row, no verb, `read` included. `grant` is user-only.

## Checking

`base grants check --subject agent:archiver --verb write --path entities/acme.md`
→ GRANTED/DENIED + exit 0/1. Run it before any non-obvious write. A refusal never
loses data: payload stays with the caller, `refuse` log line + `_ops/needs-review.md`
block record the attempt.

## Registering (install) and revoking (removal)

At capability install: draft one row per `kb.zones` manifest entry — subject
`agent:<owner_agent>` or `capability:<id>`, object = zone glob, verbs as declared,
`grantor: user`, `granted: <today>`, `via: <capability>@<version>`. Rows land **only
after the user approves the install diff**. At removal: delete rows whose `via`
matches, append a `resolve` log line, re-run `base lint`. Expect the audit to flag
the removed capability's *historical* writes still inside its window — revocation is
not retroactive amnesty; the `resolve` log line is the answer, and the findings age
out of the window.

## Enforcement, honestly

Three layers, weakest to strongest: (1) self-check at write time (this lookup — catches
honest mistakes); (2) the weekly lint's audit — `git log` authorship × this table
(per-agent git identity is configured at init; a write with no matching row is a
finding every time; tool-made `bootstrap`/`auto-sync` commits are exempt and covered by
the log.md cross-check instead); (3) the future permission gate at the harness layer
(same vocabulary). Inside one user's harness agents are cooperating processes; across
trust boundaries, enforcement is the gate's job. On **shared** bases: agent writes land
as review-queue proposals, never directly — and every read surface (search, links,
recall) honors this table too.
