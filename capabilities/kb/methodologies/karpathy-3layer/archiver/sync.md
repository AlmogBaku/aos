# kb-sync — the 5-minute git loop

Mechanical, no judgment. For each registered KB with `sync: rebase-5min`: run the
methodology's `scripts/kb-sync.sh` with the KB path as argument.

The script (not you) does: stage everything → commit if dirty (`auto-sync: <ts> (<N>
files)`) → `git pull --rebase` (**abort on conflict — never resolve**; append a
`sync-conflict` line to the KB's `log.md` and exit non-zero so the failure surfaces) →
push. Distinct exit codes per stage; success is silent.

Where the harness supports script-only scheduled jobs (Hermes: `--script --no-agent`),
materialize this schedule as one — no LLM in the loop at all. This prompt exists for
harnesses that can't, and for the `manual` degraded mode ("run the sync now").

You never resolve a sync conflict. A conflicted KB stays aborted-clean and the user hears
about it in their next brief.
