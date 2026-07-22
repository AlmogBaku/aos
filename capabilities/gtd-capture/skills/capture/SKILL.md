---
name: capture
description: Instant capture to inbox. Use when the user fires off a thought, task, idea, or voice note to capture — never classify synchronously; capture is dumb and fast.
---

# capture

1. Resolve the target KB with the kb `route` skill. Never ask the user where it goes.
2. Append one line to that KB's inbox per [sections/entry-format.md](sections/entry-format.md).
   Content verbatim — no cleanup, no summarizing.
3. Apply the user's capture preferences from MOD.md: {{mod: capture_preferences}}
4. Confirm with a single emoji. No echo, no follow-up questions.

Hard limit: under 5 seconds from message to confirmation. No lookups, no dedup checks, no
clarifying questions on this path.
