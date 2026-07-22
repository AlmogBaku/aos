# kb-sync

For each registered KB with `sync: rebase-5min`: run
`methodologies/karpathy-llm-wiki/scripts/kb-sync.sh <kb-path>`.

The script stages, commits if dirty, `git pull --rebase` (aborts on conflict, logs
`sync-conflict`, exits non-zero), pushes. You never resolve a sync conflict — a
conflicted KB stays aborted-clean and surfaces in the user's next brief.

Where the harness supports script-only jobs (Hermes: `--script --no-agent`), materialize
this schedule as one — no LLM in the loop. This prompt is for harnesses that can't, and
for `manual` degraded mode.
