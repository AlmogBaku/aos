---
name: capture
description: Instant capture, no classification. Use when the user fires off a thought, task, idea, or voice note to capture — never classify synchronously; capture is dumb and fast.
x-aos-origin: gtd-capture@0.2.0
---

# capture

1. Resolve the target KB with kb's `route` skill. Never ask the user where it goes.
2. Write it: `base --base <name> capture --text <verbatim content> --source <channel>`
   — frontmatter, sha256 dedup, `triage: pending`, and the log line come free from the
   tool (the same call kb's own `route` skill makes). Content verbatim — no cleanup, no
   summarizing.
3. A correction to something already captured is a new capture, never an edit — see the
   `gtd-capture` entry skill's `reference/entry-format.md` for the convention.
4. Apply the user's capture preferences from MOD.md: Confirm every capture with a single 🦜 emoji — nothing else, ever. Never echo the captured text back.
5. Confirm with a single emoji. No echo, no follow-up questions.

Hard limit: under 5 seconds from message to confirmation. No lookups, no clarifying
questions on this path — classification is the drain's job, not this one's.
