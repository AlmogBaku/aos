# entry-format reference — what capture composes, and the corrections rule

## Contents
- What `--text` composes
- Corrections are new captures, never edits

## What `--text` composes

`base capture` writes the frontmatter, sha256 dedup, `triage: pending`, and the log
line for free — the same tool call kb's own `route` skill uses. The capture skill only
ever supplies two things on the command line:

```
base --base <name> capture --text "<verbatim content>" --source <channel>
```

- `--text`: the content, verbatim — no cleanup, no summarizing, no reformatting.
  Long content (a transcript, forwarded text longer than a paragraph) still goes
  through the same call; the tool doesn't care about length, so there is no separate
  long-form path to remember.
- `--source`: channel provenance — `whatsapp`, `voice`, `chat`, or `<agent>:<ref>` for
  agent-originated captures.

Everything else — the filename, dedup, `triage: pending`, the log line, and (once
`route` runs) the `kb_routing` record — is the tool's and the route skill's job, never
gtd-capture's to hand-roll.

## Corrections are new captures, never edits

A correction to something already captured is **never** an edit to the existing raw
file's *content* — the captured text itself, and its provenance fields
(`source`/`source_sha256`/`captured_at`/`kb_routing`), are immutable once written. Fire
the correction as a new capture, with the content itself making clear what it supersedes
(e.g. leading with "correction: …" or naming the thing being corrected) so the drain can
find and apply it. Drain handles corrections first in its pass, same as any other
capture, oldest pending first.

This does **not** forbid bookkeeping edits to a pending file's own frontmatter by the
agent that owns that bookkeeping — drain's `meta.gtd_triaged` flag, and the archiver's
later `triage` flip at promotion, both hand-edit frontmatter in place (kb's own archiver
has no dedicated tool verb for this either). What's immutable is the captured content
and its provenance; what's mutable is the small set of bookkeeping fields each pass
owns, touched by nothing else.

This is the one rule that survives from the old `format-entry` skill — dissolved,
because its actual job (hand-rolled line format, tag-append rules) is now the tool's
frontmatter, for free.
