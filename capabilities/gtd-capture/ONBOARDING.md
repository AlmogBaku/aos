---
questions:
  - id: capture_channels
    prompt: Which channels should capture listen on?
    type: list
    required: true
  - id: reminder_target
    prompt: Where should reminders reach you?
    type: string
    required: true
  - id: drain_hour
    prompt: What time should the nightly drain run?
    type: string
  - id: inbox_kb
    prompt: Which KB's inbox should captures land in by default (or leave it to the router)?
    type: string
  - id: action_format
    prompt: How do you like next-actions phrased?
    type: string
---

# gtd-capture interview

Runs at install, after the kb and global interviews (their answers are context — don't
re-ask the timezone).

1. **`capture_channels`** — "Where do you fire off thoughts? WhatsApp to your agent, voice
   notes, the chat here?" Channel names as the harness knows them (the cheat-sheet's
   channel binding is built from these). Each channel named here also becomes a routing
   rule candidate for the kb registry.
2. **`reminder_target`** — one delivery target ("whatsapp", "chat", a channel id). Explain
   the degraded mode honestly if the harness has no outbound messaging.
3. **`drain_hour`** — default 23:00 (`HH:MM`). If they pick something after midnight,
   confirm which day's entries that means. The materialized cron uses this; kb's archiver
   files 30 minutes later, so anything within half an hour of 23:30 gets a heads-up that
   the two passes will be reordered.
4. **`inbox_kb`** — most users should leave this empty ("router decides — uncertain goes
   to your default KB"). A non-empty answer becomes an explicit capability hint the router
   honors as an explicit tag.
5. **`action_format`** — show two examples and let them react: "verb-first: 'Email Sam
   the deck'" vs "context-tagged: '@computer Email Sam'". Their phrasing preference —
   including anything idiosyncratic — is exactly what the body prose is for.
6. Capture-confirmation preferences ("just a ✅", "use a specific emoji", "no
   confirmation at all") are nuance → body, under `## Capture preferences` (the
   `{{mod: capture_preferences}}` slot quotes it).
