Open one new source-interview session in the user's desktop. That is the whole job: you are an unattended cron agent — do not interview, do not answer anything, do not touch the editorial workspace.

Use {{skill: open-session/open-session}} exactly once, with: the fenced block below as the **opening prompt**, verbatim; **skills for the new session** — {{skill: structured-interview/structured-interview}}, {{skill: ghostwriter}} and {{skill: ingest}}, which belong to the opened session, not to this run; **workdir** — `{{mod: editorial_workspace}}`; **profile** — the one this job runs in.

Return open-session's report as your final response, unchanged, a failure included: no retry, no second session, no interview here.

```text
A new source-interview session has just been opened for you on a schedule. The person reading this is the
source and the final editor; nobody else will answer, and your first message is all they see until they
reply here.

Identity for the interview record: source_surface: cli; source_conversation_id: this session's own id — the Session ID
in your system prompt, else the harness's session-id environment variable (on Hermes, HERMES_SESSION_ID);
source_thread_id: none; source_caller_id: aos:ghostwriter:source-interview; return_mode: direct; text only.

This first turn is non-interactive: do not call any ask/clarify/question tool — put any choice in plain
prose and stop. If an interview for this caller id is active, say so in one line and offer resume or fresh
in prose, then stop. Otherwise start one per the interview skill you were given — public-safe,
evidence-backed specifics from the user's recent work — persist the record, then ask exactly ONE open
question and stop: no options, no lists, no answering it yourself.
```
