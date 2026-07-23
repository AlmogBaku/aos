# weekly-lint

For each registered base:

1. `base lint --write-report` — the deterministic catalog runs in the tool; the
   report lands in `_ops/lint-report-YYYY-WW.md` with its log line.
2. Read the report. Mechanical fixes you may apply directly: rebuild the index
   (`base index rebuild`), archive stale seedlings the report names (move to
   `_archive/`, log `archive`). Judgment findings (Contested inventory, duplicate
   suspicions, unverified-with-inbound, grants-audit hits) → surface in
   `_ops/needs-review.md` with evidence and a stated default; never resolve them
   yourself.
3. Surface **Critical** findings for the user's next brief — only Critical.
4. Nothing to report → output exactly `ARCHIVER: lint clean.` and deliver nothing.
