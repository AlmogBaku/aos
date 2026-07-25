# _ops/ — the base's machinery (shared content)

- `needs-review.md` — judgment calls, refusals, sync conflicts, eviction proposals,
  failed captures. Appended by agents and the tool; **drained by the user** (or their
  chief-of-staff agent). The archiver never resolves its own judgment calls.
- `needs-entity-queue.md` — unresolved `@mentions` awaiting deliberate entity
  resolution (never auto-stubbed).
- `lint-report-*.md` — written by `base lint --write-report` on the weekly schedule.

Derived caches do NOT live here — they go to `.base/` (gitignored, rebuildable).
