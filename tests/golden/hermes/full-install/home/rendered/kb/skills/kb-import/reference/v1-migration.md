# Old-methodology KB → base — the known mapping

## Shape markers

A `SCHEMA.md` at root plus a `state/` directory (and usually `ops/inbox.md`) is the
pre-redesign methodology layout. `kb import survey` detects it.

## The mapping table (propose, then confirm with the user)

| source | destination | treatment |
|---|---|---|
| `SCHEMA.md` TYPES vocabulary | `.kb/base.yml` `types` | seed the target's types at init |
| `raw/**` | `_raw/**`, flattened | copy — already provenanced (`source_sha256` preserved); content never rewritten. Old triage values are dropped: location is the state now, and everything copied here is ingested by definition |
| `entities/ concepts/ comparisons/ queries/ projects/ domains/` | wiki zones per the agreement | **transform** (rules below) |
| `ops/inbox.md` list lines | captures | one `kb capture` per line |
| `state/STATE.md`, `PIPELINE.md` | `.kb/state/<principal>.yml` | **the state conversation** (below) |
| `state/SOUL.md`, `NORTH_STAR.md`, `CAREER.md` | `profile/` pages | transform — slow-tempo pages, not attention items |
| `state/LEARNINGS.md` | wiki pages (usually `concepts/`) | transform; split by topic if large |
| old machinery and archive directories, `.backup.*`, sync logs | skipped | GAP-note anything that looks load-bearing |

## Transform rules for wiki-bound pages

- **Frontmatter**: `updated` → `timestamp`; drop `slug` (the path is identity), `confidence`
  (superseded by `verified`, whose vouch comes from the agreement rather than the old
  field), and any growth-stage field (nothing reads it — `expires:` is the only lifetime
  rule kb has). Keep `title`, `tags`, `aliases`. Add `description` — one line, and write it
  properly, it feeds the index. Add `origin:` and `source_sha256`. `type` must exist in the
  target's types.
- **Body**: current truth only — restate facts as they stand now; past values worth keeping
  become dated `## Timeline` events in the last section; `Contested` blocks survive as
  contested; inline provenance links re-point at the copied `_raw/` paths.
- **Links**: rewrite `[[old/paths]]` to target paths. A link to something not imported stays
  and gets a GAP note — a red link is not-yet-written knowledge, not an error.
- **Do not set `expires:` on anything you import.** Nobody decided these were time-bound.

## The state conversation

Never migrate state mechanically. Read the old `STATE.md` (and `PIPELINE.md`) with the user
and ask, item by item: *is this still where your head is?* Yes → `kb state add` with a fresh
`since:` and a ref into the migrated pages. No → the knowledge is already in the wiki pages,
so there is nothing to do. "Sort of" → add it with a **`review_by:`**.

**`review_by:` is not `expires:` and must never be migrated into it.** `review_by` means
*ask me about this again*; `expires` means *`kb prune` deletes this*. They are opposites,
and a mechanical field rename here turns "remind me about this" into "throw it away".

The cap applies. If the old state has more items than fit, that is the conversation working
as designed.
