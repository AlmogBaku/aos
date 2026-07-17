# Capability: router

**Tags:** infra · **Build order:** 10 · **Seam it proves:** front-door intent dispatch across personas; adopt-native-vs-provide decision

## The problem it solves

You talk to one front agent (for Almog, that agent is "Anakin" on WhatsApp). Behind it live many capabilities, some with their own personas (personal trainer, time-blocker, interviewer). Without a dispatcher, mode-switching feels like **multiple-personality disorder** — disconnected replies, wrong persona answering, context bleeding between modes. The KB's rolling-window state helps *continuity* (any persona can cold-start into "where things stand"), but not *dispatch* — someone still has to decide which persona/profile/sub-agent handles this message. Several team members have built exactly this internally; it belongs in the kit.

## Scope

The front-door dispatcher: reads the user's message + conversation context, decides which installed capability/persona should handle it (explicit wins: "trainer mode" / mentions; else rules per channel/group; else LLM intent classification), and hands off via the harness's own mechanism — profile switch (Hermes), group routing (NanoClaw), agent switch (OpenClaw). Maintains the mode across turns (sticky until exited), announces switches so the user always knows who they're talking to, and falls back to the main agent when nothing matches.

**Adopt-native rule:** some harnesses have a router built in; some don't. Where a native router exists, this capability *configures* it (registers installed personas + trigger rules into the native mechanism) rather than replacing it. Where none exists, it ships the dispatcher as a skill on the main agent. The cheat-sheet's primitive-mapping section says which world each harness is in.

**Registration contract:** capabilities that ship an agent/persona become routable automatically — the router reads the lockfile (what's installed, which agents exist) plus each capability's manifest (`agents[]`, trigger hints if declared). Installing personal-trainer makes "trainer mode" reachable with zero router reconfiguration.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

Team members' internal routers (inventory them like the permission gates — RFC-007 pattern); Hermes profile switching + the Triage subagent's channel-dispatch rules (`ops/inbound/TRIAGE_RULES.md`); NanoClaw's group-per-agent model as a native-routing example.

## Depends

`capabilities: [onboarding]` · reads the lockfile · `host:` nothing new — dispatch rides `messaging.inbound`; the native-vs-provided split is per-harness cheat-sheet knowledge.

## Onboarding sketch

Sticky-mode duration, switch-announcement style ("[trainer]" prefix vs natural), per-channel mode locks (this WhatsApp group is always trainer), escalation word to force the main agent.

## v0.1 acceptance

On one harness: "I want to plan my gym week" reaches the personal trainer persona without naming it; mode sticks across 3 turns; "back to the main agent" exits; a second installed persona becomes routable with no manual router edit. Shares the intent/rules/LLM-fallback shape with the KB router (§4.2) — one routing philosophy, two routers.
