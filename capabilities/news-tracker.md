# Capability: news-tracker

**Tags:** usecase · **Build order:** 8 · **Seam it proves:** nothing new — the "boring port" that shows the contract is cheap to use

## Scope

Subscribed sources → periodic sweep → KB ingest → curated "worth reading" surfacing on a schedule. Per-user source list, interests, and surfacing cadence live in MOD.md.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

The Scout system, nearly whole: `_ops/subagents/scout/` — `sources.md`, `ecosystem-map.md`, daily/weekly digest patterns, handoff protocol (signal routing: content hooks vs CRM triggers vs high-signal-to-user).

## Depends

`capabilities: [kb, onboarding]` · `host: cron: preferred` (sweeps; degraded: manual), `web: required` — note: `web` is not in the §5.2 host vocabulary yet; adding it here is the rule-of-two's first live test (importer's research needs it too → it graduates).

## Onboarding sketch

Sources (feeds, people, topics), sweep cadence, digest delivery channel + time, signal threshold ("tell me only if…").

## v0.1 acceptance

Port completes in ≤1 day of work using only documented contracts — if it needs a spec conversation, the contract failed the cheapness test. A second user's install tracks entirely different sources with zero shared state.
