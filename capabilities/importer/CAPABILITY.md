---
id: importer
version: 0.1.1
tags: [infra]
summary: Wraps what you already built — inventories your harness, splits mechanism from nuance, and emits a reviewable capability draft.
depends:
  capabilities: [onboarding]
skills:
  - id: import
    used_by: [main]
---

# importer

The contribution funnel (ARCHITECTURE §6). Conversational, not a CLI. **Reads the
harness, writes a draft — never mutates the live setup, never installs, never opens
PRs.**

## Install narrative

One skill, `import`, to the front agent. No interview (`depends: onboarding` is about
conventions: the emitted draft MOD.md follows the interview skill's format).

A run produces, under the user's clone: `capabilities/<id>-draft/` (package skeleton),
a draft `MOD.md` (personal nuance — never committed), and `GAP.md` (everything that
didn't map; each entry becomes a spec fix or a documented limit).
