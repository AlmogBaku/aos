---
name: init
description: Creates a new knowledge base from a methodology's init templates and registers it. Use when the user wants a fresh KB ("kb init personal"), including during bootstrap when no KB exists yet.
---

# init

`kb init <name>` — scaffold, register, schedule. Init is not done until the archiver's
schedules exist (or their degraded mode is materialized): an unscheduled maintainer means
an undrained inbox and an unenforced contract.

1. **[D]** Confirm (usually answered in the kb interview): name, path (default
   `~/<name>-kb`), remote (optional), `audience: private | shared` (default private),
   one-paragraph `purpose` (doubles as the router's LLM rubric), channel bindings.
2. **[D]** Scaffold from `methodologies/karpathy-3layer/init/`: root contract set
   (`AGENTS.md`, `SCHEMA.md`, `index.md`, `log.md`), zone `AGENTS.md` files, directory
   tree per `init/TREE.md`. Fill `{{kb_name}}`, `{{today}}`, `{{version}}`, `{{mod: …}}` slots.
3. **[D]** Git: `git init`; configure per-agent git identity (each agent commits under
   its own `user.name` — the grants audit depends on it); commit `bootstrap`; wire the
   remote if given. Append the `bootstrap` line to `log.md`.
4. **[D]** Seed the `## Grants` table: archiver maintenance rows (from this capability's
   `kb.zones`), the user root-of-authority row, the `*` registered-agents read row.
   Include in the install diff.
5. **[D]** Register in `~/aos/kb-registry.yaml` (create from this shape if missing):

```yaml
default: <name-of-default-kb>
confidence_bar: 0.7   # RFC-006
kbs:
  - name: <name>
    tag: <short-alias>   # "…:" prefix that routes here explicitly
    path: <path>
    remote: <url or null>
    sync: rebase-5min | manual | none
    audience: private | shared
    methodology: karpathy-3layer
    purpose: >
      <one paragraph — the router's classification rubric>
    inbox: ops/inbox.md
    routing:
      channels: []
      keywords: []
```

6. **Schedules — required.** Create the archiver's three jobs (nightly-promote,
   weekly-lint, kb-sync) per the harness cheat-sheet; single-owner rule applies. kb-sync
   uses `methodologies/karpathy-3layer/scripts/kb-sync.sh` (no-agent script job where
   supported). No cron host feature → materialize each prompt as an invocable skill and tell the
   user what to run and when.
7. **[D]** Verify: run the methodology lint once (must pass clean on a fresh tree).
   Report: tree, grants, registry, schedules (or degraded modes).
