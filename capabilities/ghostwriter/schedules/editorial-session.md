Open one new editorial session in the user's desktop. That is the whole job: you are an unattended cron agent — do not do the editorial work, do not answer anything, do not touch the editorial workspace.

Use {{skill: open-session/open-session}} exactly once, with: the fenced block below as the **opening prompt**, verbatim; **skills for the new session** — {{skill: ghostwriter}}, {{skill: ingest}}, {{skill: develop}}, {{skill: critique}} and {{skill: repurpose}}, which belong to the opened session, not to this run; **workdir** — `{{mod: editorial_workspace}}`; **profile** — the one this job runs in.

Return open-session's report as your final response, unchanged, a failure included: no retry, no second session, no editorial work here.

```text
A new editorial session has just been opened for you on a schedule. The person reading this is the source
and the final editor, and your first message is all they see until they reply here. This is one bounded
interaction, then you wait for them.

Identity: source_surface: cli; source_conversation_id: this session's own id — the Session ID in your system prompt,
else the harness's session-id environment variable (on Hermes, HERMES_SESSION_ID); source_thread_id: none;
source_caller_id: aos:ghostwriter:editorial-session; return_mode: direct; text only.

This first turn is non-interactive: do not call any ask/clarify/question tool — put any choice in plain
prose and stop. Read the entry skill's handoff first — always pick up from the last spot — then run its
backlog preflight with its own arguments, before any state change: blockers are reported and stop
everything. Open with one line on where we stopped, then show what is waiting for the user — the angles,
outline or section prepared since the last chat — and ask the one decision it needs, in prose. No numbered
options, no multiple-choice; never decide for the user or invent their reply. Then stop. Before this
session ends, rewrite the handoff.
```
