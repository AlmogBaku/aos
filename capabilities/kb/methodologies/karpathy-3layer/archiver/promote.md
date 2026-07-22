# nightly-promote

Re-read the KB's `AGENTS.md` and `SCHEMA.md` first — every run. Process each registered
KB with `methodology: karpathy-3layer`.

## 1. Drain the inbox

Entries older than 24h, oldest first:

1. sha256 the content; dedup match → skip silently.
2. Write `raw/captures/YYYY-MM-DD-<slug>.md` with full raw frontmatter (`source`,
   `source_sha256`, `source_at` = entry timestamp, `source_origin` = bracket token,
   `captured_by: agent:archiver`, `triage: promoted`). One entry, one file. Pointer
   entries → just update the target's `triage`.
3. `kb_routing: uncertain` entries: re-route with the route skill. Private KB → move,
   log `route`. Shared KB → propose in `_ops/needs-review.md`, never auto-move.
4. `#correction` entries: write a Layer-2 correction page linking the raw source — never
   edit raw in place.
5. Remove drained lines. Log one `promote` line per file created.

## 2. Sweep raw into Layer 2

For new `raw/` items:

- Resolve `@mentions` alias-first. Confident match → grow the entity page (`last_touch`,
  aliases, linked fact). Ambiguous → `_ops/needs-entity-queue.md`. Duplicate suspicion →
  review queue with evidence + default. Never auto-stub, never auto-merge.
- Page-or-inline: new page only at ≥2 references or user request.
- Full universal frontmatter on new/updated pages; bump `updated:`; keep `growth_stage`
  honest.
- Update `index.md` when the map changes.
- Log one line per mutation (`create | promote | flag`; `merge` only executes a struck
  review-queue decision).

## 3. Close

No changes → output exactly `ARCHIVER: nothing to promote.` and deliver nothing.
Otherwise ≤5 lines, mechanical: "Ingested N captures. Grew M pages. Queued K to review."
