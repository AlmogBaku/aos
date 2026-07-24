---
id: importer
version: 0.2.0
tags: [infra]
summary: Wraps what you already built — inventories your harness, splits mechanism from nuance, and emits a reviewable capability draft.
depends:
  capabilities: [onboarding]
skills:
  - id: importer
    used_by: [main]
---

# importer — installer's briefing

*(This document is consumed at install and not used afterwards. The runtime face of
the capability is the `importer` entry skill.)*

## What this is

The contribution funnel (ARCHITECTURE §6). Conversational, not a CLI. Reads the
harness, writes a draft — never mutates the live setup, never installs, never opens
PRs itself.

## What you materialize, and why

1. **The skill.** One skill, `importer`, to the front agent — no agents, no schedules,
   no `kb` block: the capability's entire footprint is this one conversational skill.
2. **No interview of its own.** `depends: onboarding` is about conventions, not
   questions — the draft it emits produces its own `ONBOARDING.md`, and that draft's
   `MOD.md` format follows the onboarding skill's shape.

A run produces, under the user's clone: `capabilities/<id>-draft/` (package skeleton),
a draft `MOD.md` (personal nuance — never committed), and `GAP.md` (everything that
didn't map; each entry becomes a spec fix or a documented limit).

## Contracts to preserve

- Read-only on the live harness, write-only into the draft it owns — no file moves, no
  cleanups on the live setup, ever.
- Secrets are flagged by name, never copied by value.
- The PR stays the user's to open — this capability never opens one itself.
