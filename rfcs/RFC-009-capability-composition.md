# RFC-009: Cross-capability skill dependency

**Status:** open · **Decides:** whether and how capability B's agents may use capability A's skills

## Question

Capabilities can depend on each other (`depends.capabilities: [kb]`), and some skills are written for foreign consumption — kb's `route` skill says "use when **any capability** captures or files content." But composition currently works only by **coincidence of agent**: route is `used_by: [main]` and gtd-capture's capture skill is `used_by: [main]`, so the main agent happens to hold both. There is no vocabulary for "my capability's agent needs *your* capability's skill":

- `used_by` may only name the declaring capability's own agents (ARCHITECTURE §2.2). If gtd-capture's drainer agent needed kb's route skill, nothing could express it.
- The `provides` surface graph is on §2.2's deliberately-absent list, deferred by rule-of-two.

gtd-capture→kb is real consumer #1 (its capture flow invokes kb's routing; its drain consumes kb's pending-capture view). The rule-of-two clock is ticking but has not struck: no second *cross-agent* consumer exists yet.

**Partially answered (2026-07-25):** §2.1 now gives every skill a globally unique *installed* name (`<skill_prefix><id>`), so option 1's `kb/route` qualified-reference syntax is no longer needed to *name* a foreign skill unambiguously — `kb-route` already is unambiguous, everywhere. What that does **not** settle is the grant: naming a skill was never the hard part, deciding whose agents may load it is. The options below stand.

## Options (sketch — to be developed when this RFC is worked)

1. **Extend `used_by`** to accept qualified names (`kb/route → used_by: [main, gtd-capture:drainer]`) — grants expressed by the *providing* capability. Awkward: the provider must know its consumers.
2. **A `uses` declaration on the consumer** (`gtd-capture` manifest: `uses: [{capability: kb, skill: route, agents: [drainer]}]`) — the installing LLM materializes the referenced skill into the consumer's agent workspaces. Provider stays ignorant; installer does the join.
3. **Do nothing** — composition stays main-agent-mediated; document the constraint honestly.

## Evidence to gather before deciding

- Does gtd-capture's drainer (or any second capability's agent) actually need a foreign skill, or is main-agent mediation sufficient in practice? (Build 3–4 will show.)
- What do harnesses' native skill-scoping mechanisms allow — can a Hermes profile/OpenClaw agent load a skill from another capability's directory without copying?

## Evidence gathered (2026-07-24, gtd-capture migration)

Build 3 (gtd-capture) answered the first evidence question. Its drainer agent does need
something from kb — but a **tool**, not a **skill**. `drain` calls `base inbox` /
`base inbox --failed` (kb's capability-shipped executable, on PATH after kb's own
install, §2.4) directly as a shell command; it never loads kb's `route` or `kb`
SKILL.md content. Composition happens through the tool's process boundary, not through
`used_by`. **No cross-agent skill need surfaced** — main-agent mediation (option 3
above) remains sufficient in practice for this consumer, because the shared
infrastructure is a program on PATH, not a prompt to load. The second evidence question
(harness-native skill-scoping across profiles) is still open. This narrows what build 3
actually needed; it does not resolve the RFC.

## Process

Deferred to its own session (deliberate — raised during the kb redesign, 2026-07-23, not solved there). Decide before build 4 (importer) if gtd-capture's build surfaces a real cross-agent need; otherwise decide by build 9.
