---
id: open-session
version: 0.1.0
tags: [infra]
summary: An unattended run opens a new, titled, user-visible chat session in the harness seeded with an opening prompt, so the user continues it in their desktop or CLI instead of the job transcript.
skills:
  - id: open-session
    used_by: [main]
---

# open-session — installer's briefing

Any cron job can open exactly one new titled session in the user's desktop Recents, seed it with a prompt,
and report the session id and first reply. The seed is stored hidden, so the session opens with the agent's
message and the user continues it there, not in the job transcript. Schedule-agnostic: each consumer's job
carries its own schedule, attaches only this skill, and its `--deliver` flag is the only notification. The
conversation's own skills travel in the opening request, so cross-capability attachment is deliberate here.
`open_command` is derived at install from `reference/<runtime>.md`, never asked. Symlink the render into
every profile whose jobs call it; a requested skill missing on disk exits 2 before any session exists.
