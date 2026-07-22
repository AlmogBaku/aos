# AGENTS — _ops/ (KB metadata)

The KB's own bookkeeping. Archiver-owned except where a row says otherwise.

| file | producer → consumer |
|---|---|
| `needs-review.md` | archiver writes, user drains |
| `needs-entity-queue.md` | any agent appends unresolved `@mentions`; archiver's entity-resolve drains (high-confidence auto, ambiguous → review queue) |
| `lint-report-YYYY-WW.md` | weekly lint output |
| `backlinks-index.json` | rebuilt weekly; path → [inbound paths]; feeds orphan detection + tree promotion |
| `entity-index-<subdir>.md` | auto-generated MOCs, rebuilt weekly |
| `sync.log` / `sync-errors.log` | the sync script (gitignored, self-trimmed) |
| `secrets/` | gitignored; never committed |

## Review-queue block format (needs-review.md)

Queue-with-default + strike-to-acknowledge — unanswered items decay safely to their stated
default:

```markdown
## YYYY-MM-DD — <kind: e.g. entity merge>
**File:** <path-a> vs <path-b>
**Question:** <one-line judgment call>
**Evidence:** [[raw/...]], [[raw/...]]
**Default:** <what happens if nobody answers>. Override below ↓
```

The user answers inline, then strikes the whole block with `~~`. Struck blocks are never
re-processed. Only this format in this file — other producers (e.g. a permission gate's
denial records) get their own file, not this one.

## lint-report format

One `## <check>` section per check class (count + file list), with a `## Critical` rollup
at top (drain SLA breach, grants-audit violations, schema breakage). Critical items bubble
into the user's next brief; the rest waits for the report.
