---
name: session
description: "Opens one new titled session for the person, or adds a turn to the session that asked for the work, through `aos-session`. Use when a cron job must start a conversation the person continues on their own time, or when finished background work must reach the person in the session where they asked for it. Do NOT use to install, upgrade or remove a capability (that is capability-install), and does not conduct the conversation it opens."
---

# session

`aos-session` runs the harness's own command line from the household's cheat-sheet. Report
what it printed; the conversation itself is the person's.

## open — a new session

```
aos-session open --profile <agent> --title "<2–5 word subject> · <YYYY-MM-DD>" \
  --prompt-file <file> [--workdir <dir>] [--skills <name>]…
```

- The opening prompt is one short line the person reads first — put instructions in the skills
  the session loads, never in the prompt. Write it to a temp file with the file tool; never on
  the command line.
- The tool appends the local time to the title (a harness may reopen a title that exists). No
  `#` in a title.

## notify — the session that asked

```
aos-session notify --profile <agent> --session <id> --prompt-file <file> --title "<title>"
```

Adds the prompt as a new turn in session `<id>`. While the harness reports it busy (another turn
is running), it retries every 30 s for up to 10 minutes. Only when the harness reports that session
gone does it open a new one under `--title`.

## Report

Reply with the tool's output unchanged — on success its first line is `Opened "…" (session …)`,
`Added to session …`, or `Session … is gone; opened …`; on a failure it is `[CRON_FAILURE]`.
Exit codes: 0 ok · 1 the harness command failed · 2 bad input or no harness record · 4 not
supported on this harness · 124 timeout (the session may still exist). Never retry, never open a
second session, never answer the prompt yourself.
