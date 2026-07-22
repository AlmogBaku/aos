---
name: capture
description: Instant capture to inbox. Use when the user fires off a thought, task, idea, or voice note to capture — never classify synchronously; capture is dumb and fast.
---

# capture

Capture the user's item verbatim into the routed KB inbox.

1. Resolve the target KB with the kb `route` skill (explicit tag wins; then channel/keyword
   rules; the router handles the rest). Never ask the user where it goes.
2. Append one line to that KB's inbox, formatted per
   [sections/entry-format.md](sections/entry-format.md). Verbatim content — clean up
   nothing, summarize nothing; the drain does the thinking tonight.
3. Apply the user's capture preferences from MOD.md: {{mod: capture_preferences}}
4. Confirm with a single emoji, nothing more. No echo, no "captured!", no follow-up
   questions. If routing was uncertain, the entry carries the uncertainty tag — that is
   the drain's problem, not the user's.

Budget: under five seconds from message to confirmation. Anything that would slow that
down (lookups, dedup checks, clarifying questions) is forbidden on this path.
