# Lifecycle reference — pages, captures, trust

## Contents
- Universal page frontmatter
- Current-truth doctrine
- Timelines
- Capture triage states
- Trust: verified + origin
- Growth stages & archive

## Universal page frontmatter

```yaml
---
title: "Acme Corp"
description: Mid-market SaaS client, in pilot since May.   # one line — feeds index.md
type: company                  # from BASE.yaml types (closed; edit BASE.yaml first)
created: <DATE>
timestamp: <DATE>          # last meaningful change (bump on content edits only)
tags: [client, active]
aliases: ["Acme", "ACME"]      # variant spellings; cheaper than duplicate pages
verified: false                # agent-written pages start false; `base verify` flips
origin: raw/captures/<DATE>-call.md   # where this page came from
growth_stage: seedling         # optional: seedling | sapling | tree
meta: {}                       # free per-doc fields; used 2+ times → promote to
                               # BASE.yaml frontmatter.extensions
---
```

Identity is the file path (no slug field); filenames are lowercase-hyphen-ASCII and
never change. Raw captures additionally carry `source`, `source_sha256`, `captured_at`,
`captured_by`, `triage`, and (when routed) `kb_routing`.

## Current-truth doctrine

Wiki pages state what is true **now**. A fact changes → the line changes; the old value
lives in `git log -p`, not in the page. No supersession fields, no strikethrough. A
retracted rumor = corrected current truth + (if the event matters) one timeline line.
The one unresolved marker is **Contested**: sources disagree → record both candidates
with their sources, inline, until the user resolves it. Never resolve by guessing.

## Timelines

Added to a page **only when it needs one** — an append-only ledger of dated events
below a `---` divider, each line `- YYYY-MM-DD — <event> ([[raw/source]])`. Events stay
true as events; the timeline is never a museum of old facts. It must be the last
section of the page.

## Capture triage states

`pending` (awaiting the nightly drain) → `done` (promoted/routed/archived) — or
`failed` (error recorded in `meta.error`, surfaced in the review queue; never silently
retried forever). Immutability begins after triage: pending items may be re-routed
(logged `git mv`); a `done` file is never edited or moved again.

## Trust: verified + origin

Two fields, one rule. Agent-written pages start `verified: false`; the user's
confirmation (`base verify <page>`) flips it — a logged, deliberate act. **Never build
conclusions solely on unverified pages** (an unverified hunch may be *mentioned*
downstream, not silently become the foundation of other pages). `origin:` points every
promoted page back at its source capture; with raw's sha256 dedup this makes promotion
idempotent — the same capture can never mint the same page twice.

## Growth stages & archive

`seedling` (stub, expected to grow) → `sapling` (substance + ≥2 outbound links) →
`tree` (mature, ≥5 inbound, edit cautiously). A seedling >30 days with no growth is
lint-flagged: grow it or move it to `_archive/` (nothing is ever hard-deleted).
Page-or-inline: a concept earns a page only when referenced from ≥2 places or on
explicit request.
