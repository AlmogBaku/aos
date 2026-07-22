# nightly-promote — the archiver's synthesis pass

You are the archiver (see your persona). Re-read the KB's `AGENTS.md` and `SCHEMA.md`
first — every run, no exceptions. Work one registered KB at a time (registry entries with
`methodology: karpathy-3layer`).

## 1. Drain the inbox

Parse `ops/inbox.md` entries older than 24 hours, oldest first. For each line:

1. Compute sha256 of the content; skip on dedup match (log nothing for skips).
2. Write `raw/captures/YYYY-MM-DD-<slug>.md` with full raw frontmatter (`source`,
   `source_sha256`, `source_at` from the entry timestamp, `source_origin` from the bracket
   token, `captured_by: agent:archiver`, `triage: promoted`). One entry, one file — unless
   the entry is a pointer to an existing raw file (then just update its `triage`).
3. Entries tagged `kb_routing: uncertain`: re-run routing with the day's context (the
   route skill, drain mode). A better home in a **private** KB → move, log `route`. A
   better home in a **shared** KB → propose in `_ops/needs-review.md`, never auto-move.
4. `#correction` entries: apply to the page/raw file they supersede (Layer-2 correction
   page linking the raw source — never edit raw in place).
5. Remove drained lines from the inbox. Log one `promote` line per file created.

## 2. Sweep raw into Layer 2

For new `raw/` items since last run:

- Resolve `@mentions` alias-first. High-confidence match → grow that entity page
  (`last_touch`, aliases, a linked fact). Ambiguous → `_ops/needs-entity-queue.md`.
  Duplicate suspicion → review queue with evidence + default. Never auto-stub, never
  auto-merge.
- Respect **page-or-inline** (≥2 references or user request, else inline in parent).
- New/updated pages get full universal frontmatter; bump `updated:`; keep `growth_stage`
  honest (the lint checks the transitions, don't inflate).
- Update `index.md` when a new page changes the map.
- Log one line per mutation (`create | promote | merge* | flag`) — canonical grammar,
  composed mechanically. (*merge only executes a review-queue decision the user struck.)

## 3. Close

If the run changed nothing: output exactly `ARCHIVER: nothing to promote.` and deliver
nothing (silence gate — no empty reports). Otherwise your report is the mechanical
librarian's voice, ≤5 lines: "Ingested N captures. Grew M pages. Queued K to review."
Judgment calls you couldn't make are already in the review queue with defaults — do not
also chat about them.
