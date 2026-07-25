# Stage 3 — Map

Each clustered artifact → its package primitive (ARCHITECTURE §2.1):

| found on the harness | becomes |
|---|---|
| skill folder | `skills/<id>/` (`used_by` = which agent loaded it) |
| scheduled job | `schedules[]` — neutral 5-field cron; prompt body → the `prompt_ref` file |
| agent/profile | `agents/<name>.agent.yaml` — §2.3 neutral fields only; dropped harness tuning → GAP if load-bearing |
| persona/identity fragment | context content in the relevant skill or agent `purpose` |
| KB conventions | `kb/` templates + `kb.zones` / `kb.writes` |
| script a job runs | shipped file the schedule's prompt invokes |
| inline secret | `{store, key}` reference + GAP entry |
| maps to nothing | GAP entry |

Two artifacts competing for one slot = drift: pick the live one, GAP the other.
