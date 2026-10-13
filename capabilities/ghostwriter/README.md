# ghostwriter

Content the user is the source of. Someone has the raw material — interviews, KB notes, a week
of real work — and never turns any of it into a published post. ghostwriter removes the blank
page and owns exactly one path: grounded abstracts → angles → an outline → a draft, one section
at a time → critique → channel variants → a bundle the user posts themselves. Every step stops for
the user's choice; nothing jumps ahead to a full draft.

The line that shapes the capability is authority. The user is the source, the voice and the
final editor; the agent does retrieval, framing, drafting, flagging and repurposing. So every
claim in a draft points at a source or stays visibly marked `needs-confirmation`, every use of
private source material needs explicit clearance rather than a quiet anonymization, and the
terminal state is `approved-manual-publish`. Nothing here posts or schedules anything.

Five skills and its own agent, one editorial workspace behind a single mutation lock, and no
storage of its own: the KB owns sources, the workspace owns active editorial state.

| Skill | Job |
|---|---|
| `ghostwriter` | the map: the backlog preflight, the state machine, which skill for which request |
| `ghostwriter-ingest` | interviews and KB sources become 2–4 abstracts, each with an evidence map |
| `ghostwriter-develop` | a selected abstract becomes three angles, then an outline, then a draft one section at a time — each step waits for the user |
| `ghostwriter-critique` | grounding, sensitivity, structure, voice, and the final humanization pass |
| `ghostwriter-repurpose` | an approved anchor becomes native Blog/LinkedIn/X variants, claims unchanged |

Two chats a week, and work in between. The sourcing and developing schedules never hold the
conversation: each uses [`open-session`](../open-session/) to open one titled session in the
user's own desktop — the interview seeded with its first question, the developing one with what is
waiting for a decision — and stops; the user answers there, on their own time. Between them an
unattended run (`develop-ahead`) opens nothing and messages no one: it turns new material into
angles and moves each chosen piece one gated step forward. A workspace `HANDOFF.md`, read first and
rewritten last by every chat and run, is how each chat picks up from the last spot, and each
interview closes on one concrete next task. Delivery is a notification only; `local` is silent.

Requires [`kb`](../kb/) for sources, [`structured-interview`](../structured-interview/) for the
interview path, and [`open-session`](../open-session/) for the two chat schedules — the last two
granted to its agent with `uses`, so `capability-lifecycle` 0.4.0 or later.

## Support matrix

| Harness | Status | Runner |
|---|---|---|
| Hermes | 🧪 built against the cheat-sheet and dogfooded in the author's household — live e2e owed | @AlmogBaku |
| NanoClaw (v1+v2), OpenClaw, Nanobot | 🧪 cheat-sheet shipped, research-drafted — no runner yet | — |
| Claude Code, OpenCode | 📋 no sheet yet — the no-cheat-sheet path applies | — |

`cron` is `preferred`, not required, and both chat schedules reach the user through
`open-session`, so their support is `open-session`'s: on a harness where a scheduled run cannot open
a session, the `degraded: manual` path is the real one — every skill still works when the user asks
for it, and the two sessions simply never open themselves. Without cron the background run is
skipped (`degraded: skip`), and the work it would have done waits for the next chat.
