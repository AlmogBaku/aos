# session

Opens a session for the person, or continues the one that asked for the work. A weekly cron
job opens *"Start this week's source interview."* in the person's session list; a guest
interview that ends adds *"the memo is approved — here it is"* as a new turn in the very
conversation where the person created the invite, and opens a fresh session only when that one
is gone.

Two commands, `aos-session open` and `aos-session notify`, and no harness code: the household's
cheat-sheet says how the harness does each step, and the tool fills the template and runs the
harness's own command line. When a harness changes a flag, one line of its sheet changes.

| Harness | Status | Runner |
|---|---|---|
| Hermes | ✅ open and continue probed live (2026-10-20); unread marking of a continued session is verified in the live e2e | @AlmogBaku |
| Claude Code, Codex, OpenClaw, Nanobot | 🧪 `mapping.session` is `support: unknown` — the research notes in each sheet say how it could work | — |
| NanoClaw | ✗ no titled sessions — the sheet says what to do instead | — |

Install: see [CAPABILITY.md](CAPABILITY.md). Usage: [skills/session/SKILL.md](skills/session/SKILL.md).
