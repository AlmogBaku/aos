# Wiring reference — schedules, cron, degraded modes

## Contents
- The three schedules
- Wiring the tool per harness
- Degraded modes

## The three schedules

| id | kind | when | what |
|---|---|---|---|
| `nightly-promote` | agent (archiver) | 23:30 | drain pending captures → skeptical promotion (after gtd-capture's 23:00 drain) |
| `weekly-lint` | agent (archiver) | Sat 07:00 | `base lint --write-report` per base + judgment surfacing |
| `sync` | **exec** | */5 min | `base.py sync --all` — script-direct, **no LLM wakes up** |

Single-owner rule: each schedule runs in exactly one harness at a time.

## Wiring the tool per harness

The tool is harness-blind (registry/BASE.yaml in; files + exit codes out). Per-harness
variance is **composition in the wrapper the installing LLM writes**, per the
cheat-sheet:

- Invocation: `uv run <clone>/capabilities/kb/skills/kb/scripts/base.py …`
  (uvx/pipx fallback; `uv` is a one-line install if missing).
- Cron: e.g. Hermes `hermes cron create … -- uv run …/base.py sync --all` as a
  script-only job.
- Surfacing: optionally compose a notifier around the exec call:
  `… sync --all || <harness-notify "base sync needs attention">`. The file bus
  (`_ops/needs-review.md`, `log.md`, exit codes) is the portable interface either way.
- Env: `AOS_REGISTRY` (registry path), `AOS_AGENT` (acting subject for log lines).

## Degraded modes

- No cron on the harness: all three schedules become `manual` — invocable run-cards;
  tell the user what to run and when ("run `base sync --all` when you finish a
  session"; "ask the archiver to promote nightly").
- No uv/python: the tool's contracts are performed by hand per each base's AGENTS.md
  (capture frontmatter + sha256 + log line; grants lookup by reading the table; lint
  by checklist). Slower, same rules — the files remain the contract.
