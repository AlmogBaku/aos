---
name: lint
description: The karpathy-llm-wiki methodology's deterministic KB checks. Use when running the weekly lint schedule, when adopt needs a divergence report, or when the user asks for a KB health check.
x-aos-origin: kb@0.1.3
---

# lint

Execute every check exactly; a check you can't run mechanically on this KB is reported
"not checkable", never guessed.

**Schema**
1. Layer-2 pages: frontmatter parses; universal fields present; `type` in the SCHEMA.md
   vocabulary; `slug` == filename; per-type extras present.
2. `state/` files: minimal header (`updated:`, `maintainer:`); char budget respected
   (state/AGENTS.md table).
3. Filenames: slug rules; date-stamped patterns where required.

**Hygiene**
4. `.backup.*` / `*.bak` anywhere → **Critical**.
5. Per-run status/heartbeat files in `ops/` or `state/` → pollution count.
6. Empty pages outside the calendar-preseed exception.
7. Project pages outside `projects/`.

**Links & growth**
8. Broken wikilinks.
9. Orphan pages (zero inbound, >30 days).
10. Stale seedlings (>30 days, no growth); stage claims vs actual inbound counts.
11. Tags used <2 times.
12. Contested-flagged and `confidence: low` pages (surface, don't fix).

**Log & audit**
13. `log.md` grammar: every line below the header parses as the five-field format with a
    legal verb; violations listed per line.
14. Grants audit: `git log --since=<last lint>` authorship × `## Grants` — every commit
    touching a zone must be by a subject holding `write` there → violations **Critical**.
15. `updated:` header vs actual last-commit date on state files.
16. Two authors on one `state/` file in the window.

**Liveness**
17. Drain SLA: age of oldest inbox entry — >24h finding, >48h **Critical**.
18. Schedules alive: last `promote`/`lint` log lines within expected cadence — a silent
    maintainer is **Critical**.

**Output**: `_ops/lint-report-YYYY-WW.md` — `## Critical` rollup first, then one
`## <check>` section per non-empty check (count + file list). Adoption mode (invoked by
the adopt skill): same checks, report to chat, write nothing into the KB.
