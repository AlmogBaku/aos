# aos — the batteries for your agent harness

> `aos` is a placeholder name — [RFC-001](rfcs/RFC-001-naming.md) picks the real one.

**Harnesses are batteries-not-included. This kit is the batteries** — a curated set of capabilities (knowledge base, GTD capture, time blocking, daily briefing, news tracking, voice, a personal trainer someone already built…) that install into the agent harness you already run — Hermes, NanoClaw, OpenClaw first; Claude Code, OpenCode next — personalize themselves to you through an onboarding interview, and keep your personalization intact across upgrades.

**The kit is two things: a protocol — the backbone — and a set of implementations.** It's not that complicated; the new software is a prompt. The protocol is the agreement on how a capability is shipped, changed, and kept updated. The implementations are the capabilities: markdown, scripts, a thin infra layer that is at bottom prompts — and where real code is needed, standalone programs behind process boundaries. Once the backbone lands, everybody just contributes implementations — that's how this does more than any of us could alone.

## Install

Paste into your agent:

> Clone https://github.com/AlmogBaku/aos to ~/aos, read ~/aos/harnesses/&lt;your-harness&gt;/CHEATSHEET.md and ~/aos/docs/BOOTSTRAP.md, then set me up.

That's the whole funnel — your harness's own agent performs the install, guided by its [cheat-sheet](harnesses/hermes/CHEATSHEET.md) (Hermes first; more to come) and [BOOTSTRAP.md](docs/BOOTSTRAP.md). No CLI, no adapter code.

## Why this is open source

The harness companies — and a wave of startups on top of them — are commercializing exactly this layer: the built-in building blocks, the chief-of-staff, the second brain. We are builders. We build this anyway, for ourselves, on whatever harness we each run — and we're not going to pay rent on our own work, to them or to anyone productizing it.

A chief of staff is not something that should live inside some company's proprietary IP. It's something everybody should have. Turning it into a product is not our job; keeping it a commons is. That's why the concepts, the contracts, and the batteries are open — MIT, one repo, belonging to the people who build with them.

## The one story to keep in mind

A team member's personal-trainer capability, built in their own Hermes: they *ask their agent* to import it into the kit → PR → you ask your agent to install it → onboarding interviews *you* (your goals, your gym days, your injuries) → your harness runs *your* version → the author's next release merges in without touching your nuances. **Wrap → share → install → personalize → upgrade.**

Note there's no CLI doing this: `aos import` / `aos install` are conversational — you ask your harness agent in plain language, and it follows the relevant capability's skill. The kit is a protocol and a set of prompts, not a program. Every contract in this repo exists to make that loop work.

## Read in this order

1. [ARCHITECTURE.md](ARCHITECTURE.md) — the spec. §1 for the story, the seven problems, and the mental model; §3 is the one inviolable contract (the overlay); §8 is the decision index: every decision is either a **firm position + rationale** or an **RFC**.
2. [rfcs/](rfcs/) — the eight open decisions: naming, testing, governance, install bookkeeping, MOD.md persistence, multi-KB routing/authorization, permission-gate vocabulary, agent-comms opinionation. (The last three are the contested cores of the kb, permission-gate and agent-comms capabilities — their build plans proceed; their contested behavior follows the RFC.)
3. [capabilities/](capabilities/) — one-pagers for the eleven reference capabilities and the build order.
4. [design/](design/) — the concrete deep-dives where the spec's contracts become exhibits: [capability anatomy](design/capability-anatomy.md) (a real capability, file by file), [install flow](design/install-flow.md) (every step, deterministic vs agentic marked), [KB methodology](design/kb-methodology.md) (the 3-layer knowledge model, schema, growth stages, synthesis, retrieval), [KB authorization](design/kb-authorization.md) (routing, grant tables, sequence diagrams, worked multi-KB cases), [agent-comms](design/agent-comms.md) (agent→agent envelope, glass-box rule, transports, guards).
5. [prior-art.md](prior-art.md) — where this sits vs gstack (closest on architecture) and PAI/LifeOS (closest on domain), and the square neither occupies.

## How to engage

- Disagree with a firm position → open an issue naming the section, **with a counter-proposal**.
- Weigh in on RFCs before their auto-accept deadlines (RFC-003 defines the default window).
- The fastest way to move anything: build against it. A working PR outranks an RFC comment.

## License

MIT.
