# Capability: gtd-capture

**Tags:** usecase · **Build order:** 3 · **Seam it proves:** first vertical composing on kb + schedules; first real routing traffic

## Scope

Voice/text capture → `ops/inbox.md` in the routed KB → nightly drain promotes to next-action / KB zones / reminders. Capture is dumb and fast (no synchronous classification); the drain does the thinking. Multi-KB routing happens on the capture path via the kb router.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

- Capture format + skill: the `anakin-capture` skill (enforces entry format into `~/ai-kb/ops/inbox.md`).
- Drain: Archiver's nightly 23:00 promotion pass.
- The inbox-pattern itself: `ops/inbox.md` conventions in `~/ai-kb/ops/AGENTS.md`.

## Depends

`capabilities: [kb, onboarding]` · `host: messaging.inbound: required` (capture arrives via chat/voice), `cron: preferred` (drain; degraded: manual).

## Onboarding sketch

Capture sources (which channels), reminder delivery target, drain hour, per-KB inbox mapping (or accept router defaults), next-action format preferences.

## v0.1 acceptance

A WhatsApp voice capture lands in the right KB's inbox < 5s; nightly drain files it; the personal-trainer-style cross-check: a second user installs with different answers and gets a differently-wired but working capture path.
