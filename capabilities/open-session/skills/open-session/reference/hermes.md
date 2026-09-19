# open-session on Hermes

`open_command`:

```
<hermes venv>/bin/python <home>/personal/capabilities/open-session/skills/open-session/scripts/open_session.py --profile {profile} --title {title} --prompt-file {prompt_file} {skills} --workdir {workdir}
```

`<hermes venv>/bin/python` is the interpreter behind the `hermes` launcher (here
`~/.hermes/hermes-agent/venv/bin/python`): the script imports `hermes_state`, which only that
interpreter resolves. `{skills}` is one `--skills NAME` per skill, empty for none; `{title}` is one
shell-quoted argument. The script then runs `hermes -p {profile} --cli {skills} --pass-session-id
chat --in {workdir} -c {title} --create-if-missing --source cli -Q --query-file {prompt_file}`.

- `-c <title> --create-if-missing` is the only supported way to create a *new titled* session: a title miss mints one with `source="cli"`.
- No `#` in a title: lookup prefers the newest `"<title> #N"` lineage row over the exact match, so a `#` silently resumes an old session (`hermes_state_titles.py:167-176`).
- `-Q` is a one-shot quiet turn: the reply lands on stdout, `session_id: <id>` on **stderr** (`cli.py:4209`) — the script parses the last such line.
- `--skills` is a global flag, and Hermes only *warns* on an unknown name unless every name is unknown — hence the on-disk `SKILL.md` check before launch.
- `-p default` is the root profile home; any other name is `<root>/profiles/<p>`, and its skills live under `<profile home>/skills/<name>`.
- The env scrub drops the cron run's `HERMES_SESSION_*` / `HERMES_CRON_SESSION` / `HERMES_CRON_AUTO_DELIVER_*` bindings, or the new session inherits the cron run's identity.
- A title the profile already holds would be *resumed*, so the script re-checks it with Hermes' own lookup (`SessionDB.resolve_session_by_title`) and appends a local-clock ` HH:MM` on a hit (` HH:MM:SS` if that minute is taken too); the title it actually used is on stderr as `title: <t>`.
- `display_kind='hidden'` (`hermes_state_messages.py:364`) makes the desktop transcript and the sidebar preview skip the seed while the model still reads it; a failed hide is one `warning:` line, never a failure.
- The opened session is left unread: `set_session_read(session_id, read=False)` writes the `last_read_at=0.0` watermark (a NULL one counts as *read*, `hermes_state_sessions.py:917`), and `touch_session_activity(..., description=<reply's first line>)` gives the unread row something to preview.
- Exit codes: 0 opened; 2 a requested skill is missing on disk, or the child failed / printed no `session_id:`; 124 timeout — the session may still exist.

Named `hermes.md`, not `harness-hermes.md`: this is a skill compile source, not a
capability-lifecycle cheat-sheet (which the linter holds to six sections).
