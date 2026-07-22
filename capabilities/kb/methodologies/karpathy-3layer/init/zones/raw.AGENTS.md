# AGENTS — raw/ (Layer 1)

Immutable sources. Append-only; **only archiver skills write here** (captures arrive via
`ops/inbox.md` and are promoted in).

- **sha256 dedup on every ingest** — recompute, compare, skip on match.
- **One source per file.** A meeting transcript and the email confirming the meeting are
  TWO files. Emails: one file per thread.
- Frontmatter: universal + the `raw/` extras (`source`, `source_sha256`, `source_at`,
  `source_origin`, `captured_by`, `triage`).
- Never edited in place. A wrong fact gets a Layer-2 correction page linking back here.

| subdir | holds |
|---|---|
| `captures/` | promoted inbox entries (voice notes, drive-by thoughts) |
| `clippings/` | saved articles/snippets |
| `meetings/` | transcripts/notes, one per meeting |
| `emails/` | one file per thread |
| `calendar/` | event exports (feeds entity pre-seeding) |

Retention: captures older than 30 days with zero inbound wikilinks move to
`_archive/captures/<year>/` (weekly lint does it, logs `archive`). Everything else stays
forever.
