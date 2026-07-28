"""Vocabulary the rest of the tool reads: verb names, frontmatter field sets, and the
one regex that recognises a wikilink. Extracted verbatim, comments included — moving
this module changes nothing any sibling tool sees (tools/lint/checks/skill-names.mjs
and tools/lib/constants.mjs only ever match CLI-invocation strings like `kb capture` in
prose, never this file's Python set literals)."""

import re

VERSION = "0.7.0"
LAYOUT = 2
# `kb init`'s default template source — a plain, read-only, unauthenticated clone;
# --template overrides it, --templates (local dir) skips the network step entirely.
TEMPLATE_REPO_URL = "https://github.com/AlmogBaku/aos-kb-template"
# The closed `aos-verb` trailer vocabulary — the same words the five-field log.md
# grammar used, now carried by the commit that made the change.
AOS_VERBS = {
    "create", "promote", "merge", "archive", "flag", "resolve", "sync-conflict",
    "lint", "route", "refuse", "capture", "state", "verify", "bootstrap",
    "ingest", "pending", "prune", "set", "config", "migrate",
}
UNIVERSAL_FIELDS = {"title", "description", "type", "created", "timestamp", "tags",
                    "aliases", "verified", "origin", "meta", "expires", "review_by"}
RAW_FIELDS = {"source", "source_sha256", "captured_at", "kb_routing",
              "captured_by", "source_origin", "corrects"}
# .kb/pending/ — one file per item. A queue FILE is only justified when the work item
# has no artifact of its own; a refusal and a sync conflict are the only two things
# with nothing to attach to, because nothing was written and nothing was committed.
PENDING_KINDS = {"capture", "refusal", "conflict", "entity", "finding"}
WAITS_ON = {"agent", "human"}
PENDING_FIELDS = {"kind", "waits_on", "raised_by", "failed"}
WIKILINK_RE = re.compile(r"\[\[([^\]|#\n]+?)(?:[|#][^\]]*)?\]\]")
# Dedup is scoped to the acting principal: same principal, same sha256, no new file —
# import/capture idempotency depends on it, and the flaky-client double-send is the
# common case. It is NOT global: on a base several people share, a global scan drops a
# second person's identical capture and discloses the first person's path.
