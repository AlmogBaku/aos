# Capability: ptt-mode

**Tags:** infra · **Build order:** 6 · **Seam it proves:** the `voice.*` host vocabulary

## Scope

Voice-in-voice-out interaction mode as an installable capability: a skill that switches a session into PTT (short spoken turns, TTS replies, transcript capture to KB), wrapping whatever STT/TTS the host exposes. Consumed by interviewing, brainstorming, time-blocking negotiation.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

Fragmented but real: ElevenLabs v3 TTS (Almog's daily-briefing voice notes), DeepDub/ElevenLabs wiring in OpenClaw env, a Slack PTT interview flow (Hera, Almog's content agent) + `sag` TTS, `audio_cache/` conventions, the Telnyx softphone (`~/phone/`) for actual calls (out of v0.1 scope — noted as a future adapter of the same vocabulary).

## Depends

`capabilities: [onboarding]` · `host: voice.stt: required, voice.tts: required` — this capability *defines* the honest degraded story: no voice features ⇒ not installable, and the support matrix says so plainly.

## Onboarding sketch

Voice choice, language(s), speaking pace, transcript retention (which KB), wake/trigger convention per channel.

## v0.1 acceptance

One PTT session end-to-end on Hermes (Slack) with transcript landing in the routed KB; interviewing (build 7) consumes it unmodified.
