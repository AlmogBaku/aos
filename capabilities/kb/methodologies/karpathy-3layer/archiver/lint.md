# weekly-lint

For each registered karpathy-3layer KB:

1. Run every check in `lint/SKILL.md`. Write `_ops/lint-report-YYYY-WW.md`
   (`## Critical` rollup first).
2. Rebuild `_ops/backlinks-index.json` and the `_ops/entity-index-*.md` MOCs.
3. Growth stages: promote pages whose inbound counts qualify; flag stale seedlings —
   never delete.
4. Retention: 30-day zero-inbound `raw/captures/` → `_archive/captures/<year>/`; drafts
   >30 days → `_archive/`. Log `archive` per move.
5. Log one `lint` line with the report path.
6. Surface Critical findings for the user's next brief — only Critical. Nothing to
   report → output exactly `ARCHIVER: lint clean.` and deliver nothing.
