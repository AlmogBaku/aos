---
name: authz-check
description: Looks up whether a subject may perform a verb on a KB zone, using that KB's Grants table. Use when routing a write, registering or revoking a capability's zones, or auditing whether an observed write was authorized.
x-aos-origin: kb@0.1.0
---

# authz-check

One ACL for the whole kit (§4.3): **subjects × objects × verbs**, stored per-KB as the
first markdown table under `## Grants` in that KB's `AGENTS.md`. The permission-gate
capability reads the same table at the messaging layer — never invent a second format.

## The table

| column | meaning |
|---|---|
| `subject` | `user` · `agent:<name>` · `capability:<id>` · `*` (any *registered* subject) |
| `object` | git-style glob(s) relative to the KB root |
| `verbs` | subset of `read write route-into grant` (space-separated) |
| `grantor` | who granted (v0.1: always `user`) |
| `granted` | ISO date |
| `via` | `<capability>@<version>` for install-time grants, else `—` |
| `notes` | semantics prose (e.g. "append-only", "rewrite whole file") |

## Checking

1. Read the target KB's `AGENTS.md`, find the `## Grants` table.
2. A subject holds a verb on a path iff some row matches subject (exactly, or `*` for any
   registered subject), the path matches the row's glob, and the verb is listed.
   **Default posture is deny: no row, no verb.** `read` is never assumed either.
3. An unknown/unregistered agent matches nothing (not even `*` rows). Its write is refused;
   refusal preserves data (see the route skill).
4. `grant` itself is held by `user` only in v0.1 — capabilities *request* rows at install
   (drafted by the installer, shown in the diff gate, approved by the user); no delegation,
   no admin agents.

## Registering / revoking (install & removal time)

- Install: draft one row per `kb.zones` entry — subject `agent:<owner_agent>` (or
  `capability:<id>` for capability-level grants), object = the zone glob, verbs it needs,
  `grantor: user`, `granted: <today>`, `via: <capability>@<version>`. Rows land only after
  the user approves the install diff.
- Removal: delete exactly the rows whose `via` matches the capability being removed (the
  lockfile knows), append a `resolve` line to `log.md`, re-run the KB lint.
- **"Cross-zone writes require updating this table first"** — the one-line rule that makes
  the table load-bearing. A write without a pre-existing row is a violation the weekly
  audit (git-diff × grants) will catch, per-agent git identity making attribution
  mechanical.
