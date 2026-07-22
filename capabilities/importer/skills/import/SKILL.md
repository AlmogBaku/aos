---
name: import
description: Imports an existing use case from this harness into an aos capability draft. Use when the user asks to wrap, package, export, or contribute something they already built ("import my trainer setup into the kit").
---

# import

Reverse-engineer a personalized install back into template + overlay. Read-only on the
live harness; you write only drafts under the user's clone.

Rules:
- Never modify the live setup — no file moves, no cleanups.
- Secrets: flag by name, never copy a value. Inline secret → `{store, key}` reference +
  GAP entry.
- Unsure whether something is mechanism or nuance → nuance side (draft MOD.md) + a GAP
  note.

Copy this checklist and work the stages in order:

```
- [ ] 1. Inventory — sections/inventory.md
- [ ] 2. Cluster — sections/cluster.md
- [ ] 3. Map — sections/map.md
- [ ] 4. Split — sections/split.md
- [ ] 5. Emit — sections/emit.md (GAP format: sections/gap-report.md)
```
