# AGENTS — entities/ (Layer 2)

Synthesized pages for people, companies, communities, products. Archiver-maintained;
corrections welcome from any granted agent.

Page lifecycle:

1. **Pre-seed** — calendar events create seedling stubs *before* captures mention the
   entity (the empty-page exception in SCHEMA.md). This is the cheapest entity-sprawl
   killer: the stub exists, so mentions resolve instead of spawning duplicates.
2. **Grow** — the first `[[mention]]` expands the stub: aliases, `role`/`org`,
   `last_touch`.
3. **Mature** — ≥5 inbound links promotes to `tree` (the weekly lint computes inbound from
   the backlinks index).

Rules:

- **Alias-first matching**: before creating any entity page, search existing `aliases:`.
  Adding an alias is cheaper than letting two pages exist for one entity.
- **Merges are never automatic.** Suspected duplicate → `_ops/needs-review.md` with
  evidence and a stated default. Conflating two people is expensive to undo.
- Unresolved `@mention` → `_ops/needs-entity-queue.md`, never an auto-stub.
