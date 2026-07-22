---
name: import
description: Imports an existing use case from this harness into an aos capability draft. Use when the user asks to wrap, package, export, or contribute something they already built ("import my trainer setup into the kit").
---

# import

You are reverse-engineering a *personalized install that never had a template* back into
template + overlay. This is the inverse of the install transform, and harder — pure
judgment. You only read the harness; you write only drafts under the user's clone.

Ground rules: **read-only** on the live setup (no file moves, no cleanups, however
tempting); **secrets are flagged, never copied** — an inline token becomes a
`{store, key}` reference plus a GAP entry; when mechanism and nuance are hard to
separate, put it in the draft MOD.md and note the doubt (nuance in the skeleton pollutes
every future user; mechanism in MOD just costs the author a copy-paste later).

Work the five stages in order — each stage's section carries the detail:

1. **[Inventory](sections/inventory.md)** — enumerate what exists, guided by the
   cheat-sheet's Introspection section.
2. **[Cluster](sections/cluster.md)** — group artifacts into candidate use cases; confirm
   scope with the user ("just the trainer, or the meal-planning cron too?").
3. **[Map](sections/map.md)** — each artifact → its package primitive.
4. **[Split](sections/split.md)** — generic mechanism → skeleton; personal nuance → draft
   MOD.md. The core value; do it sentence by sentence, not file by file.
5. **[Emit](sections/emit.md)** — write `capabilities/<id>-draft/` + draft MOD.md +
   [GAP.md](sections/gap-report.md); run the tier-1 lint on the draft if the repo's
   tools are present; hand the author their punch list.
