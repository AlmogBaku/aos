---
name: authz-check
description: Looks up whether a subject may perform a verb on a KB zone, using that KB's Grants table. Use when routing a write, registering or revoking a capability's zones, or auditing whether an observed write was authorized.
x-aos-origin: kb@0.1.3
---

# authz-check

One ACL kit-wide: **subjects × objects × verbs**, the first markdown table under
`## Grants` in each KB's `AGENTS.md`. The permission gate reads the same table — never
invent a second format.

| column | meaning |
|---|---|
| `subject` | `user` · `agent:<name>` · `capability:<id>` · `*` (any *registered* subject) |
| `object` | git-style glob(s) relative to the KB root |
| `verbs` | subset of `read write route-into grant`, space-separated |
| `grantor` | who granted (v0.1: always `user`) |
| `granted` | ISO date |
| `via` | `<capability>@<version>` for install-time grants, else `—` |
| `notes` | semantics (e.g. "append-only", "rewrite whole file") |

**Check**: subject holds verb on path iff a row matches subject (exact, or `*` for
registered subjects), glob matches path, verb is listed. **Default deny: no row, no
verb** — `read` included. Unregistered agents match nothing, not even `*`; their writes
are refused (refusal preserves data — see the route skill).

`grant` is held by `user` only. Capabilities request rows at install; the user approves
via the diff gate. No delegation.

**Register (install)**: draft one row per `kb.zones` entry — subject
`agent:<owner_agent>`, object = zone glob, needed verbs, `grantor: user`,
`granted: <today>`, `via: <capability>@<version>`. Rows land only after diff approval.

**Revoke (removal)**: delete rows whose `via` matches the removed capability, append a
`resolve` line to `log.md`, re-run the KB lint.

Cross-zone writes require a row here **first**. The weekly lint audits `git log`
authorship against this table.
