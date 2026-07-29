# Lifecycle reference — pages, captures, trust

## Contents
- Universal page frontmatter
- Current-truth doctrine
- Timelines
- Capture states
- Trust: verified + origin
- End of life

## Universal page frontmatter

```yaml
---
title: "Acme Corp"
description: Mid-market SaaS client, in pilot since May.   # one line — feeds index.md
type: company                  # from .kb/base.yml types (closed; edit that file first)
created: <DATE>
timestamp: <DATE>          # last meaningful change (bump on content edits only)
tags: [client, active]
aliases: ["Acme", "ACME"]      # variant spellings; cheaper than duplicate pages
verified: false                # agent-written pages start false; `kb verify` flips it
origin: _raw/<DATE>-call.md    # the capture this page came from
expires: <DATE>            # optional — the ONLY thing kb knows about lifetime
metadata: {}                   # free per-doc fields; used by 2+ docs → graduate to
                               # .kb/base.yml frontmatter.extensions
---
```

Identity is the file path — there is no slug field, and filenames are
lowercase-hyphen-ASCII and never change. Raw captures additionally carry `source`,
`source_sha256`, `captured_at`, `captured_by`, and (when routed) `kb_routing`. A capture
that errored keeps `failed: <error>`.

## Current-truth doctrine

A wiki page states what is true **now**. A fact changes, the line changes; the old value
lives in `git log -p`, not in the page. No supersession fields, no strikethrough. A
retracted rumour is corrected current truth plus, if the event itself matters, one timeline
line. The single unresolved marker is **Contested**: sources disagree, so record both
candidates inline with their sources until the user resolves it. Never resolve by guessing.

## Timelines

Added to a page only when it needs one — an append-only ledger of dated events below a
`---` divider, each line `- YYYY-MM-DD — <event> ([[_raw/source]])`. Events stay true as
events; a timeline is never a museum of old facts. It must be the page's last section.

## Capture states

**Location is the state.** In `.kb/pending/` means waiting; `kb ingest <path>` — a
base-relative path, as `kb inbox` prints it, not a bare id — moves it to
`_raw/`, which means ingested and immutable. There is no separate field to disagree with the
directory the file sits in. A correction is a new capture linked to the old one —
`kb capture --corrects <path>` — never an edit, and never prose that a later pass has to
match by inference. A capture that errors keeps `failed: <error>` and stays put; it is
never silently retried forever.

## Trust: verified + origin

Two fields, one rule. Agent-written pages start `verified: false` and the user's
confirmation (`kb verify <page>`) flips it — a logged, deliberate act. **Never build a
conclusion solely on unverified pages**: an unverified hunch may be *mentioned* downstream,
but it must not silently become the foundation of other pages. `origin:` points every
promoted page back at its source capture, and with raw's sha256 dedup that makes promotion
idempotent — the same capture can never mint the same page twice.

## End of life

Two mechanisms, and they stop looking like a conflict once you see the split. `expires:` is
a date **someone set deliberately**, so honouring it is deterministic and `kb prune`
deletes, reporting what went; git is the undo. An eviction is a **judgment** that something
stopped mattering, so the archiver proposes it and a human decides — `kb archive <page>
--reason …`, a `git rm` plus an attributed commit carrying the reason. Declared end-of-life
versus judged end-of-life: neither the archiver's caution nor prune's decisiveness has to
bend, and there is no archive directory because the commit captures strictly more.

Page-or-inline is the other half of the same economy: a concept earns a page only when
referenced from ≥2 places or on explicit request.

`review_by:` is a third thing and must never be confused with `expires:` — it means *ask me
about this again*, where `expires:` means *delete this*. They are opposites.
