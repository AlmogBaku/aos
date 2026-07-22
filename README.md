# aos — the batteries for your agent harness

> `aos` is a placeholder name — [RFC-001](https://github.com/AlmogBaku/aos/blob/spec/rfcs/RFC-001-naming.md) picks the real one.

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

## What's on this branch vs the spec

**`main` is the kit** — the built artifacts: [capabilities/](capabilities/) (built
capability directories), [harnesses/](harnesses/) (per-harness cheat-sheets, Hermes
first), [docs/](docs/) (BOOTSTRAP, TESTING, the build-gap ledger), [tools/](tools/) +
[tests/](tests/) (tier-1 lint, golden renders, transcripts).

**The [`spec` branch](https://github.com/AlmogBaku/aos/tree/spec) is the spec** — the
reference-on-paper the kit is built against. Read in this order there:

1. [ARCHITECTURE.md](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md) — the spec. §1 story + mental model; §3 the one inviolable contract (the overlay); §8 the decision index: every decision is a **firm position + rationale** or an **RFC**.
2. [rfcs/](https://github.com/AlmogBaku/aos/tree/spec/rfcs) — the eight open decisions. (RFC-006/007/008 are the contested cores of kb, permission-gate, agent-comms — builds proceed; contested behavior follows the RFC.)
3. [capabilities/*.md](https://github.com/AlmogBaku/aos/tree/spec/capabilities) — one-pagers for the eleven reference capabilities and the build order.
4. [design/](https://github.com/AlmogBaku/aos/tree/spec/design) — deep-dive exhibits: capability anatomy, install flow, KB methodology, KB authorization, agent-comms.
5. [prior-art.md](https://github.com/AlmogBaku/aos/blob/spec/prior-art.md) — vs gstack and PAI/LifeOS, and the square neither occupies.

Spec corrections discovered while building land on the `spec` branch; the trail is
[docs/BUILD-GAPS.md](docs/BUILD-GAPS.md) here.

## How to engage

- Disagree with a firm position → open an issue naming the section, **with a counter-proposal**.
- Weigh in on RFCs before their auto-accept deadlines (RFC-003 defines the default window).
- The fastest way to move anything: build against it. A working PR outranks an RFC comment.

## License

MIT.
