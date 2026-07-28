# Wiring reference — schedules, cron, degraded modes

## The three schedules

| id | kind | when | what |
|---|---|---|---|
| `nightly-promote` | agent (archiver) | 23:30 | ingest `.kb/pending/` captures → skeptical promotion |
| `weekly-maintain` | agent (archiver) | Sat 07:00 | `kb prune`, then `kb lint` per base + judgment surfacing |
| `sync` | **exec** | every 5 min | `kb sync --all` — script-direct, **no model wakes up** |

Single-owner rule: each schedule runs in exactly one harness at a time. `kb prune` running
weekly is a contract other capabilities depend on — a warning window shorter than the prune
interval means items vanish before anyone can react.

## Wiring the tool per harness

The tool is harness-blind: registry and `.kb/base.yml` in, files and exit codes out. All
per-harness variance is composition in the wrapper the installing agent writes, per the
cheat-sheet.

- Installed once at capability install → the `kb` command on PATH; the lockfile records it
  and removal uninstalls it. `uv` itself is a one-line install.
- Cron: the wrapper **must anchor the registry** — export
  `AOS_REGISTRY=<home>/personal/kb-registry.yaml`, or pass `--registry`. A bare `kb sync`
  with no resolvable registry exits 0 having synced nothing, which is the silent failure.
- Surfacing: optionally compose a notifier around the exec call
  (`… || <harness-notify "kb sync needs attention">`). The file bus — `.kb/pending/`, git
  history, exit codes — is the portable interface either way.
- Env: `AOS_REGISTRY` · `AOS_AGENT` (the acting subject, committer of every write) ·
  `AOS_PRINCIPAL_ID` (overrides `<home>/.aos/kb-principal.yml` for one call).

## Degraded modes

- **No cron**: all three become `manual` run-cards — tell the user what to run and when
  ("run `kb sync --all` when you finish a session").
- **No uv or python**: perform the same contracts by hand per each base's `AGENTS.md` —
  capture frontmatter plus sha256 plus a commit, grants by reading the table, lint by
  checklist. Slower, same rules; the files remain the contract.
