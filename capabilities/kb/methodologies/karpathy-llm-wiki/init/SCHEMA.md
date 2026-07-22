# SCHEMA — {{kb_name}} conventions

> Single source of truth for frontmatter, links, naming, and tags. The archiver re-reads
> this before every ingest. Adding a `type` means editing this file FIRST, committing,
> then using it.

## Filenames

- Slugs: lowercase, hyphens, ASCII only, ≤60 chars. No spaces, no non-Latin script in
  filenames (non-ASCII belongs in `title:`/body). Filename = stable URL: it never changes.
- Date-stamped files (`raw/`, reviews): `YYYY-MM-DD-<slug>.md`. Week files: `YYYY-WW.md`.
- People: `firstname-lastname` (only-first-name-known: `firstname-orgtag`). Companies:
  hyphenated legal-ish name. Concepts: noun phrase.

## Universal frontmatter (every Layer-2 page)

```yaml
title: "…"               # human-readable; non-ASCII fine
type: concept            # from the TYPES vocabulary below
slug: matches-filename
created: YYYY-MM-DD
updated: YYYY-MM-DD
growth_stage: seedling   # seedling | sapling | tree
confidence: medium       # low | medium | high
tags: []                 # lowercase-hyphenated
aliases: []              # variant spellings — feeds the entity matcher
```

`state/` files (Layer 3) carry a minimal header instead — they are working files, not
pages:

```yaml
updated: YYYY-MM-DD
maintainer: agent:main   # single writer; lint flags two authors in a window
```

## Per-type extras

- **`raw/`**: `source` (`voice-note | email | chat | meeting | clipping | document |
  calendar`), `source_sha256` (dedup key, computed at ingest), `source_at` (full ISO
  timestamp with TZ), `source_origin` (`<platform>:<sender>`), `captured_by` (agent id),
  `triage` (`capture | promoted | archived | dropped`). **One source per file** — a meeting
  transcript and the email confirming it are two files.
- **person**: `role`, `org` (company slug), `relationship` (enum — seed:
  `prospect | client | partner | family | friend | acquaintance`; extend via your overlay,
  not ad hoc), `last_touch`.
- **company**: `domain` (which `domains/<x>/` owns it), `stage` (`active | dormant |
  dead`), `primary_contacts` (wikilink list).
- **project**: `status` (`active | waiting | blocked | done | cancelled`), `deadline`
  (ISO or null), `next_action` (string — empty next_action on an active project is a lint
  finding). Projects live in `projects/` — exactly one home.

## TYPES

`person | company | community | product | concept | comparison | query | project | review |
capture | meeting | clipping | email | session-log | plan`

## Growth stages

- **seedling** — stub, 1–3 lines. Lint flags seedlings older than 30 days with no growth:
  they grow or they archive.
- **sapling** — frontmatter + 5–30 lines + ≥2 outbound wikilinks.
- **tree** — multi-section, ≥5 *inbound* links, stable. Edit cautiously.

## Wikilinks

Full form = repo-root path, no `.md`: `[[entities/people/jane-doe]]`. Short form allowed
within the same zone when unambiguous. Unresolved `@mention` → `_ops/needs-entity-queue.md`
— never auto-stub. Adding an alias is cheaper than letting two pages exist for one entity;
merging duplicates is never automatic (review queue — conflating two people is expensive
to undo). Backlinks are computed, not written: `_ops/backlinks-index.json`, rebuilt weekly.

## Tags

Open vocabulary, disciplined: lowercase-hyphenated; a secondary index, never the primary
discriminator (if a tag is doing a field's job, it should be a frontmatter field). Weekly
lint flags tags used <2 times for merge or removal.

## Confidence & contested facts

- `low` = single source / unverified (lint-surfaced weekly) · `medium` = multiple sources,
  no contradiction · `high` = user-confirmed OR ≥3 independent sources. Never silently
  upgrade — state the reason in the body or log line.
- Contested facts: never pick a side — both values inline with provenance wikilinks and a
  bold `Contested — flagged YYYY-MM-DD` marker. Lint surfaces them weekly.

## Empty pages

Frontmatter-with-no-body is allowed only for calendar-preseeded seedling stubs.
Everything else needs at least one sentence.

## log.md

Canonical line — five fields, pipes, one line per synthesis mutation, append-only:

```
YYYY-MM-DDTHH:MM±TZ | <agent> | <verb> | <path> | <one-line summary>
```

Verbs: `bootstrap | create | promote | merge | archive | flag | resolve | sync-conflict |
lint | route | refuse`. Compose the line mechanically, exactly this grammar — the lint
validates it. Reads are never logged; sync auto-commits are not logged (git history
covers them).
