# Stage 3 — Map

Each clustered artifact → its package primitive (ARCHITECTURE §2.1):

| found on the harness | becomes |
|---|---|
| skill folder | `skills/<id>/` (Agent Skills folder, `used_by` from which agent loaded it) |
| scheduled job | `schedules[]` entry — neutral 5-field cron; prompt body extracted to the `prompt_ref` file |
| agent/profile | `agents/<name>.agent.yaml` — only the §2.3 neutral fields; harness tuning is dropped (note it in GAP if it looked load-bearing) |
| persona/identity fragment | context block content in the relevant skill or agent `purpose` |
| KB conventions (zone files, entry formats) | `kb/` templates + `kb.zones` / `kb.writes` declarations |
| script the job runs | shipped file the schedule's prompt invokes (standalone, process boundary) |
| inline secret | `{store, key}` reference + **GAP entry**; the value is never copied anywhere |
| anything that maps to nothing | GAP entry (hardcoded path, harness-only API, dead artifact) |

Two artifacts mapping onto the same primitive slot (two crons, one purpose) usually
means the live setup has drift — pick the live one, GAP the other.
