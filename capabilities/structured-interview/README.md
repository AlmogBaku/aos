# structured-interview

Interviewing as a reusable mechanism rather than a feature of whatever happens to need it. One
useful question at a time, the record rewritten after every turn, and an explicit stop
condition — so an interview survives a restart, a scheduled caller, and a user who answers
three days later.

What it owns is deliberately narrow: question craft, turn-taking, when to follow a golden
nugget and when to move on, resumability, and the InterviewRecord. What it does not own is
everything downstream. The record goes back to its caller — and into the user's KB when
`kb_mode` is configured — and the skill stops there.

The part that is easy to get wrong, and is therefore specified rather than left to judgment, is
identity. Every record carries the reply tuple it must answer on (`source_surface`,
`source_conversation_id`, `source_thread_id`), a scheduled caller's job id *alongside* that
tuple and never instead of it, and a record id derived from the tuple — so two callers cannot
collide, a retry returns the same record instead of starting a second interview, and a
scheduled run can never guess where to reply. A CLI or desktop session is its own reply tuple:
the session id is the conversation id, which is what makes an interview opened by a schedule
answerable in the session the user actually sees.

One skill, no agent, no schedule of its own: callers bring the trigger. It uses the `kb` command
on PATH when configured and degrades to a local completed record when no KB is available.

| Skill | Job |
|---|---|
| `structured-interview` | the whole capability: start, each answer, question types, completion, resume |

## Support matrix

| Harness | Status | Runner |
|---|---|---|
| Hermes | 🧪 built against the cheat-sheet and dogfooded in the author's household — live e2e owed | @AlmogBaku |
| NanoClaw (v1+v2), OpenClaw, Nanobot | 🧪 cheat-sheet shipped, research-drafted — no runner yet | — |
| Claude Code, OpenCode | 📋 no sheet yet — the no-cheat-sheet path applies | — |

`voice.stt`/`voice.tts` are `preferred`, not required: with neither, `voice_mode` falls back to
one concise text question and records `voice_fallback: text` in the turn. A harness with no
`AskUserQuestion` equivalent still gets option decisions — they are persisted as numbered
options with `next_action: await-choice` and delivered to the reply tuple.
