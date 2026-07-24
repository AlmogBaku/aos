# v1 (old-methodology) → v2 base — the known mapping

## Contents
- Shape markers
- The mapping table
- Transform rules for wiki-bound pages
- The state conversation

## Shape markers

`SCHEMA.md` at root + a `state/` directory (and usually `ops/inbox.md`) = a v1
methodology KB (the pre-redesign layout). `base import survey` detects this shape.

## The mapping table (propose, then confirm with the user)

| v1 source | v2 destination | treatment |
|---|---|---|
| `SCHEMA.md` TYPES vocabulary | `BASE.yaml types` | seed the target's types at init |
| `raw/**` | `raw/**` (same subpaths) | copy — already provenanced (`source_sha256` preserved); content never rewritten. One field translates: legacy `triage` values map `capture`→`pending`, `promoted`/`archived`/`dropped`→`done` (v2 vocabulary) |
| `entities/ concepts/ comparisons/ queries/ projects/ domains/` | wiki zones per agreement | **transform** (rules below) |
| `ops/inbox.md` list lines | pending captures | one `base capture` per line |
| `state/STATE.md`, `PIPELINE.md` | `state.yaml` | **the state conversation** (below) |
| `state/SOUL.md`, `NORTH_STAR.md`, `CAREER.md` | `profile/` pages | transform (slow-tempo pages, not attention) |
| `state/LEARNINGS.md` | wiki pages (e.g. `concepts/`) | transform; split by topic if large |
| `_ops/`, `_archive/`, `.backup.*`, sync logs | skipped | GAP-note anything that looks load-bearing |

## Transform rules for wiki-bound pages

- Frontmatter: `updated` → `timestamp`; drop `slug` (path is identity) and
  `confidence` (superseded by `verified` — the vouch comes from the agreement, not
  the old field); keep `title/tags/aliases/growth_stage`; add `description` (one
  line — write it, it feeds the index); add `origin:` (source path) +
  `source_sha256` (of the source file); `type` must exist in the target BASE.yaml.
- Body: **current truth only** — restate facts as they stand now; past values worth
  keeping become dated `## Timeline` events (last section); `Contested` blocks
  survive as contested; inline provenance links re-point at the copied `raw/` paths.
- Links: rewrite `[[old/paths]]` to target paths; a link to something not imported →
  leave it and GAP-note it (a red link is not-yet-written knowledge, not an error).

## The state conversation

Never migrate state mechanically. Read the old `state/STATE.md` (and PIPELINE) with
the user and ask, item by item: *is this still where your head is?* Yes → `base
state add` with a fresh `since:` and a `ref` into the migrated pages; no → the
knowledge is already in the wiki pages, nothing to do; "sort of" → add with a
`review_by:`. The cap applies — if the old state has more items than fit, that's the
conversation working as designed.
