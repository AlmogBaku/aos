# Capability: interviewing

**Tags:** infra · **Build order:** 7 · **Seam it proves:** capability-depends-on-capability composition

## Scope

Structured interviewing as a reusable capability: the agent leads a question-driven session (topic brief in, structured notes out to KB), used for content drafting, decision framing, retros — and it is the engine the onboarding capability's interviews run on (extracted here so both share one implementation). Optionally consumes ptt-mode for voice interviews.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

The `almog-interview` skill of Hera (Almog's content agent) — "interview me, I hate blank pages" — plus her Slack PTT interview flow; the weekly-review PTT session patterns in `ops/reviews/`.

## Depends

`capabilities: [kb, onboarding]` · optional: `ptt-mode` — the first *optional* capability dependency, which is exactly the seam this build validates (install works without it, upgrades when it appears).

## Onboarding sketch

Interview style (rapid-fire vs exploratory), pushback level, note format, default KB destination for transcripts/outputs.

## v0.1 acceptance

Same interview brief runs in text-only and PTT modes; removing ptt-mode degrades gracefully without reinstalling interviewing.
