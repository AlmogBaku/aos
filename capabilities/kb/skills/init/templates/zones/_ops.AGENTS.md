# _ops/ — the base's machinery (shared content)

- `needs-review/` — judgment calls, refusals, sync conflicts, eviction proposals,
  failed captures: **one file per entry**, written by agents and the tool and
  **drained by the user** (or their chief-of-staff agent). The archiver never resolves
  its own judgment calls. It is a directory rather than one appended file for the same
  reason the inbox is: a single file every agent on every machine appends to is
  precisely what conflicts on every sync, and distinct filenames never do.
- `needs-entity-queue.md` — unresolved `@mentions` awaiting deliberate entity
  resolution (never auto-stubbed).
- `lint-report-*.md` — written by `base lint --write-report` on the weekly schedule.

Derived caches do NOT live here — they go to `.base/` (gitignored, rebuildable).
