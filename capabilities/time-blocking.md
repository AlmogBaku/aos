# Capability: time-blocking

**Tags:** usecase · **Build order:** 5 · **Seam it proves:** `calendar.write` host feature + degraded modes

## Scope

Reads the calendar, writes time blocks for priorities, negotiates conflicts with the user (PTT if available). Respects the global MOD.md working-hours/sacred-time model — the first consumer of those fields. Conflict changes are draft-and-approve (calendar writes are externally visible).

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

- Calendar **read**: `gog` CLI (Google Workspace, both accounts authed).
- Working-hours & sacred-time source material: `state/SOUL.md` red lines, Hera persona working-hours block.
- Calendar **write path is new** — the main net-new build in the reference set.

## Depends

`capabilities: [kb, onboarding]` · `host: calendar.read: required, calendar.write: required, voice.tts: optional` (negotiation degrades to text), `scheduler: preferred` (planning pass; degraded: manual).

## Onboarding sketch

Which calendar(s), block granularity + minimum block, deep-work windows, negotiation style (ask-always vs auto-below-threshold), what is never schedulable-over (seeds sacred time).

## v0.1 acceptance

A week of blocks written and surviving a real calendar's churn; zero writes over sacred time; degraded install (no scheduler) still usable via manual invocation.
