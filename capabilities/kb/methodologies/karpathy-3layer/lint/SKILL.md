---
name: lint
description: The karpathy-3layer methodology's deterministic KB checks. Use when running the weekly lint schedule, when adopt needs a divergence report, or when the user asks for a KB health check.
---

# lint

Every check is deterministic — schema validation, glob checks, log/diff audit. Execute
them exactly; a check you can't run mechanically on this KB is reported as "not
checkable", never guessed. (Prime candidate for an RFC-004 helper tool; until then you
are the executor, and being trivially checkable is the point.)

## Checks

**Schema**
1. Every Layer-2 page: frontmatter parses; universal fields present; `type` in the
   SCHEMA.md vocabulary; `slug` == filename; per-type extras present (raw extras on
   `raw/`, `next_action` on active projects).
2. `state/` files: minimal header present (`updated:`, `maintainer:`); per-file char
   budget respected (state/AGENTS.md table).
3. Filenames: slug rules (lowercase-hyphen-ASCII, ≤60); date-stamped patterns where
   required.

**Structure & hygiene**
4. `.backup.*` / `*.bak` files anywhere → Critical (git history is the archive).
5. Loose per-run status/heartbeat files in `ops/` or `state/` → pollution count.
6. Empty pages outside the calendar-preseed exception.
7. Projects outside `projects/` → wrong-home finding.

**Links & growth**
8. Broken wikilinks (target path doesn't exist).
9. Orphan pages (zero inbound per backlinks index) older than 30 days.
10. Stale seedlings (>30 days, no growth); sapling/tree stage claims vs actual link
    counts (no inflated stages).
11. Tags used <2 times (merge/remove candidates).
12. Contested-flagged and `confidence: low` pages (surface, don't fix).

**Log & audit**
13. `log.md` line grammar: every line below the header parses as the five-field format
    with a legal verb. Violations listed per line.
14. **Grants audit**: `git log --since=<last lint>` authorship × the `## Grants` table —
    every commit touching a zone must be by a subject holding `write` there (per-agent
    git identity). Violations → Critical.
15. `updated:` staleness vs actual last-commit date on state files (a stale stamp means
    the header discipline broke).
16. Two authors on one `state/` file within the window → single-writer violation.

**Liveness**
17. **Drain SLA**: age of oldest `ops/inbox.md` entry. >24h = finding; >48h = Critical.
    (This one number would have caught the extraction source's core failure in two days.)
18. Schedules alive: last `promote` and `lint` log lines are within their expected
    cadence — a specified-but-not-running maintainer is a Critical finding, not a shrug.

## Output

`_ops/lint-report-YYYY-WW.md`: `## Critical` rollup, then one `## <check>` section per
non-empty check (count + file list). Adoption mode (invoked by the adopt skill): same
checks, report to chat instead, write nothing into the KB.
