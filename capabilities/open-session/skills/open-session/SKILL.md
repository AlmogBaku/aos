---
name: open-session
description: "Opens one new titled chat session in this harness, seeds it with the caller's opening prompt as a hidden first turn, and reports the session id plus the first reply. Use when a scheduled job must start a conversation the user continues on their own time. Does not conduct that conversation, reuse a title, or send any notification."
---

# open-session

One command opens a new titled session seeded with the caller's prompt, stored hidden so the session opens with the agent's message; report what was opened — the conversation itself is the user's.

## Inputs

- **opening prompt** — required, verbatim: never answer it, rewrite it, or shorten it.
- **skills** to preload in the new session — optional.
- **workdir** — optional; defaults to the current working directory.
- **title hint** — optional.

## Do

1. Title = the hint, else `<2–5 word subject> · YYYY-MM-DD`. No `#` anywhere: with a `#` the harness resumes an old session instead of creating one. A title this profile already holds is fine — rather than resume it, the script appends the time (` HH:MM`) and echoes what it used as `title: <t>` on stderr.
2. Write the opening prompt to a temp file with the file-writing tool — never a heredoc, never on the command line. Delete it when done.
3. Run `{{mod: open_command}}` in the foreground, timeout 600 s, capturing stdout and stderr: `{profile}` = the profile this run executes in (on Hermes, the basename of `$HERMES_HOME` when it sits under `profiles/`, else the literal `default`), `{skills}` = one `--skills NAME` per skill (no skills → empty string), `{workdir}` absolute, `{title}` shell-quoted, `{prompt_file}` = the temp path from step 2.
4. On exit 0, reply `Opened "<title>" (session <id>) in profile <p>.` — `<title>` is stderr's `title:` line, which may not be the one you passed — then a blank line, then the captured stdout verbatim. On any non-zero exit, the first line is exactly `[CRON_FAILURE]`, followed by the exit code and the stderr tail.

## Never

- Never conduct, continue, or answer the conversation you opened.
- Never retry with the same title.
- Never put the opening prompt on the command line.

The Hermes command and the reason for each of its flags: `reference/hermes.md`.
