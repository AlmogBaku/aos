---
id: importer
version: 0.1.0
tags: [infra]
summary: Wraps what you already built — inventories your harness, splits mechanism from nuance, and emits a reviewable capability draft.
depends:
  capabilities: [onboarding]
skills:
  - id: import
    used_by: [main]
---

# importer

The contribution funnel (ARCHITECTURE §6): "import my trainer use-case into the kit" is a
conversation, not a CLI. The importer **only reads the harness and writes a draft** —
it never mutates the live setup, never installs, never opens PRs.

## Install narrative

One skill, `import`, to the front agent. No agents, schedules, zones, or interview
(`depends: onboarding` is about *conventions*: the draft MOD.md it emits follows the
MOD format the interview skill defines).

## What a run produces

Under the user's clone: `capabilities/<id>-draft/` (the package skeleton — manifest,
skills, agents, onboarding sketch), a draft `MOD.md` beside it (the personal nuance,
never committed), and `GAP.md` — everything that didn't map: hardcoded paths,
harness-only APIs, flagged inline secrets (never copied), judgment calls. GAP findings
are spec food: each one either fixes a contract or documents a real limit.
