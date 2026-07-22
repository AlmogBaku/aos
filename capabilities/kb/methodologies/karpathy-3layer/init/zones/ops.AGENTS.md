# AGENTS — ops/ (capture + workflow)

The live front door. The front agent writes here; the archiver drains.

## inbox.md — the capture contract

One line per capture, appended, **nothing else in the file** (no headings, no multi-line
blocks — long content goes to a `raw/` file with a one-line pointer here):

```
- YYYY-MM-DDTHH:MM±TZ [<channel-or-agent|ref>] (#tag #tag) : <raw content>
```

- Timestamp ISO-8601 with explicit offset.
- The bracket names the source: a channel (`[whatsapp]`, `[voice]`), or `[agent|ref]` for
  agent-originated entries.
- Zero or more `#lowercase-hyphenated` tags in one paren group. Routing tags (`#work`)
  and the router's own annotations (`kb_routing: uncertain` entries) live here too.
- **Corrections are appends**: never edit a wrong entry — add a new one tagged
  `#correction` that supersedes it. Append-only capture with corrective appends.
- Capture is dumb and fast. No classification, no lookups, no questions at capture time.

**Drain SLA:** the nightly promote empties everything older than 24h. "Age of oldest
undrained entry" is a lint health metric — if it exceeds 48h the lint report's Critical
section says so. (The KB this was extracted from grew a 20KB never-drained inbox because
no metric watched it.)

## tasks/ & reviews/

- Project pages live in `projects/` (Layer 2) — `tasks/` holds working task files only.
- Reviews: `reviews/closeouts/YYYY-MM-DD.md`, `reviews/weekly/YYYY-WW.md`,
  `reviews/monthly/YYYY-MM.md`.
- Active-project cap: {{mod: project_cap}} (default 12 total). At cap, the front agent
  surfaces "pick one to park" instead of adding.
- Per-run status dumps, heartbeats, ticket mirrors: **not here** — agent workspaces exist
  for that. The lint counts loose ops/ files as a pollution metric.
