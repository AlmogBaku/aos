# Stage 1 — Intake

Understand the ask before researching it. Don't silently fill gaps — surface them.

Ask, clustering related questions and skipping what's already answered:
- What triggers it — a schedule, an inbound message, another agent's output, a manual
  ask?
- What does it read, and what does it write or send? Any host primitive involved
  (`cron`, `messaging.inbound/outbound`, `voice.stt/tts`, `calendar.read/write`,
  `email`, `secrets-store`)?
- Does it compose with anything already installed, or stand alone?
- Who approves what it does before it does it, if anything is consequential or
  irreversible?
- Scope: what's explicitly out for v0.1?

Capture answers plus any nuance beyond the literal answer — that nuance becomes
personalization content at Build time (the user's own MOD.md and the package's
interview questions — see the split rule in [build.md](build.md)), not something to
discard and never something to hardcode into the package itself.

Move to Research once the shape is clear enough to investigate, not necessarily once
every question has a final answer — some gaps are exactly what Research resolves.
