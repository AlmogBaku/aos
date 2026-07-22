---
name: init
description: Creates a new knowledge base from a methodology's init templates and registers it. Use when the user wants a fresh KB ("kb init personal"), including during bootstrap when no KB exists yet.
x-aos-origin: kb@0.1.0
---

# init

`kb init <name>` — scaffold, register, and **schedule the maintainer in the same session**.
A KB whose archiver is "installed later" decays immediately: the extraction source for this
capability had a fully specified maintainer that was never scheduled, an inbox that was
never drained, and a contract nobody enforced. Init therefore is not done until the
schedules exist (or their degraded mode is materialized).

## Steps

1. **[D] Ask/confirm the basics** (usually already answered in the kb interview): name,
   path (default `~/<name>-kb`), remote (optional), `audience: private | shared`
   (default private), one-paragraph `purpose` (doubles as the router's LLM rubric),
   channel bindings (optional).
2. **[D] Scaffold** from `methodologies/karpathy-3layer/init/`: copy the root contract set
   (`AGENTS.md`, `SCHEMA.md`, `index.md`, `log.md`), the zone `AGENTS.md` files, and create
   the directory tree exactly as `init/TREE.md` lists it. Fill the template slots
   (`{{kb_name}}`, `{{default_agents}}`, `{{mod: …}}`).
3. **[D] Git**: `git init`, configure the **per-agent git identity** convention (each agent
   commits under its own `user.name` — the weekly authorization audit depends on it), first
   commit `bootstrap`, wire the remote if given. Append the `bootstrap` line to `log.md`.
4. **[D] Grants**: seed the `## Grants` table — the archiver's maintenance rows (from this
   capability's `kb.zones`), the user's root-of-authority row, and the default rows
   (registered-agents read; unregistered agents nothing). Show in the install diff.
5. **[D] Register** in `~/aos/kb-registry.yaml` (create the file from the documented shape
   if missing — it is user-owned overlay family):

```yaml
default: <name-of-default-kb>
confidence_bar: 0.7   # RFC-006 — expect this to move
kbs:
  - name: <name>
    path: <path>
    remote: <url or null>
    sync: rebase-5min | manual | none
    audience: private | shared
    methodology: karpathy-3layer
    purpose: >
      <one paragraph — the router's classification rubric>
    inbox: ops/inbox.md
    routing:
      channels: []      # e.g. ["whatsapp:+<ID>"]
      keywords: []
```

6. **Schedules — not optional.** Create the archiver's three jobs (nightly-promote,
   weekly-lint, kb-sync) per the harness cheat-sheet, single-owner rule applying. The sync
   job uses the methodology's `scripts/kb-sync.sh` (copied per cheat-sheet script
   conventions, no-agent mode where supported). If `scheduler` is unavailable, materialize
   each prompt as an invocable run-card skill and tell the user what to run and when.
7. **[D] Verify**: run the methodology lint once (it must pass clean on a fresh tree) and
   report: tree created, grants seeded, registry updated, schedules live (or degraded
   modes in effect).
