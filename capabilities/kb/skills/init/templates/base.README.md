# {{name}}

A **base**: a knowledge store that is a git repo of markdown files, nothing more. No
database, no server, no export format — if the tooling vanished you would still have your
notes, in folders, in git.

## What is where

| | |
|---|---|
| `index.md` | the map — one line per page. Start here. |
| `_raw/` | source material exactly as it arrived: captures, clippings, transcripts. Flat, and immutable once ingested. |
| `entities/` `concepts/` `projects/` `profile/` | the wiki — one page per thing, stating **what is true now**. Changed your mind? The line changes; the old value is in `git log -p`. |
| `AGENTS.md` | the contract your agents read before writing. Its Grants table is the one place that says who may write where. |
| `.kb/` | the tool's own bookkeeping. Don't hand-edit it. |

## What you actually do

```
kb capture --text "…"        file a thought — takes under a second
kb search "acme"             full-text
kb find --where type=person  filter by frontmatter
kb pending list --where waits_on=human    what is waiting on you
kb state show                where your head is
```

Everything else is your agents' job. They ingest what you captured, grow pages, and put
anything they are unsure about in `.kb/pending/` for you.

## Two things worth knowing

**Pages link with `[[double brackets]]`.** Pages get moved and reorganised constantly; a
wikilink survives that, a path does not. A `[[link]]` with no page behind it is not a
mistake — it means "mentioned, not written up yet".

**Deletion is opt-in.** A page lives forever unless it carries `expires:`, and past that
date `kb prune` removes it and tells you what went. Git is the undo, always.
