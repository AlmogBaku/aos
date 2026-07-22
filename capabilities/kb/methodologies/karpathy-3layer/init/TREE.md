# The tree `kb init` creates

Copy the four root files + per-zone AGENTS.md files from `init/`, then create:

```
<kb-root>/
  AGENTS.md  SCHEMA.md  index.md  log.md
  raw/            captures/  clippings/  meetings/  emails/  calendar/
  entities/       people/  companies/  communities/  products/
  concepts/
  comparisons/
  queries/
  projects/                    # ONE home for project pages (see SCHEMA per-type)
  domains/                     # created empty; per-domain dirs get their own AGENTS.md
                               # row + zone file when a domain maintainer is declared
  state/
  ops/            tasks/  reviews/closeouts/  reviews/weekly/  reviews/monthly/
  drafts/
  _ops/
  _archive/       captures/
```

Also:

- `ops/inbox.md` — created empty with the one-line-per-capture header (see ops/AGENTS.md).
- `.gitignore` — `_local/`, `_ops/secrets/`, `_ops/sync.log`, `_ops/sync-errors.log`,
  session caches.
- `.gitattributes` — LFS for binaries (`*.pdf *.png *.jpg *.zip *.mp3 *.mp4`) if git-lfs
  is available; otherwise note its absence in the init report.
- Empty dirs hold a `.gitkeep`.
- Do **not** create per-run status/heartbeat files anywhere — agents keep those in their
  own workspaces outside the KB (AGENTS.md write rules).
