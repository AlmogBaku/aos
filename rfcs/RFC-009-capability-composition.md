# RFC-009: Cross-capability skill dependency

**Status:** resolved 2026-10-12 (proposed — closes after the dogfood period) · **Decides:** whether and how capability B's agents may use capability A's skills

## Resolution: option 2 — a consumer-side `uses` grant

A capability whose **own** agent loads another capability's skill declares the grant itself:

```yaml
uses:
  - {capability: kb, skill: route, agents: [steward]}
```

The installer links the provider's existing render into each listed agent's skill location, under the provider's *installed* name, and records that link under the **consumer's** lockfile entry (`uses_links`, kept apart from the consumer's own `links` because link basenames are name claims). The provider's install, upgrade and removal never create, move or delete it; every lockfile link has exactly one owner, and recording a path another entry already holds is refused. `used_by` keeps naming only the declaring capability's own agents. A file that only a non-main agent reads and that references a foreign skill without a grant is a lint error; a file `main` also reads stays silent, because `main` composes through the provider's own `used_by: [main]` link. The `provides` surface graph stays on §2.2's absent list — `uses` is the narrow grant, not a graph.

**Why the consumer and not the provider (option 1).** A provider should not have to know its consumers: option 1 turns every new consumer into an edit to the provider, and the incident below was precisely a provider's own bookkeeping deciding where a consumer's link lived.

**Evidence, first question** — *does any agent actually need a foreign skill?* Yes. A use-case capability's own agent ran scheduled jobs that load a session-opening skill from one infra capability and an interview skill from another; mediating through `main` was not what happened in practice. With no way to declare the grant, the links were made by hand and recorded on the providers' entries. A provider upgrade then re-derived its links from its own `used_by: [main]`, moved the link to the front agent, and the consumer's jobs reported success for about two weeks while opening nothing (`docs/BUILD-GAPS.md`, 2026-10-05, on `main`).

**Evidence, second question** — *can a harness load a skill from another capability's directory without copying?* Yes on Hermes: a profile reads only its own `skills/` directory and follows symlinks there, so a grant is one more symlink into the grantee's profile. The other harnesses scope `used_by` either by directory or by a per-agent `skills:` list, and `uses` is materialized the same way `used_by` is on each.

**Rule of two.** Two machine readers exist on `main` (`aos-cap manifest`/`record` and the `uses/*` lint family, capability-lifecycle 0.4.0). The first in-repo declarer is the contributed ghostwriter capability, once it declares its agent. Built ahead of this resolution, on a branch, as a documented gap — which is what this section closes.

## Question

Capabilities can depend on each other (`depends.capabilities: [kb]`), and some skills are written for foreign consumption — kb's `route` skill says "use when **any capability** captures or files content." But composition currently works only by **coincidence of agent**: route is `used_by: [main]` and gtd-capture's capture skill is `used_by: [main]`, so the main agent happens to hold both. There is no vocabulary for "my capability's agent needs *your* capability's skill":

- `used_by` may only name the declaring capability's own agents (ARCHITECTURE §2.2). If work-tracker's steward agent needed kb's route skill, nothing could express it.
- The `provides` surface graph is on §2.2's deliberately-absent list, deferred by rule-of-two.

work-tracker→kb is real consumer #1 (its capture flow invokes kb's routing; its steward consumes kb's pending-capture view). The rule-of-two clock is ticking but has not struck: no second *cross-agent* consumer exists yet.

**Partially answered (2026-07-25):** §2.1 now gives every skill a globally unique *installed* name (`<skill_prefix><id>`), so option 1's `kb/route` qualified-reference syntax is no longer needed to *name* a foreign skill unambiguously — `kb-route` already is unambiguous, everywhere. What that does **not** settle is the grant: naming a skill was never the hard part, deciding whose agents may load it is. The options below stand.

## Options (sketch — to be developed when this RFC is worked)

1. **Extend `used_by`** to accept qualified names (`kb/route → used_by: [main, work-tracker:steward]`) — grants expressed by the *providing* capability. Awkward: the provider must know its consumers.
2. **A `uses` declaration on the consumer** (`work-tracker` manifest: `uses: [{capability: kb, skill: route, agents: [drainer]}]`) — the installing LLM materializes the referenced skill into the consumer's agent workspaces. Provider stays ignorant; installer does the join.
3. **Do nothing** — composition stays main-agent-mediated; document the constraint honestly.

## Evidence to gather before deciding

- Does work-tracker's steward (or any second capability's agent) actually need a foreign skill, or is main-agent mediation sufficient in practice? (Build 3–4 will show.)
- What do harnesses' native skill-scoping mechanisms allow — can a Hermes profile/OpenClaw agent load a skill from another capability's directory without copying?

## Evidence gathered (2026-07-24, and re-confirmed 2026-07-29 against work-tracker)

Build 3 answered the first evidence question, and answered it the same way twice — once as
`gtd-capture` and again as its successor `work-tracker`, which is the stronger result because
the two capabilities were designed independently.

Its own agent does need something from kb — but a **tool**, not a **skill**. The steward calls
`kb find --where …`, `kb set` and `kb inbox` (kb's capability-shipped executable, on PATH after
kb's own install, §2.4) directly as shell commands; it never loads kb's `route` or `kb`
SKILL.md content. Composition happens through the tool's process boundary, not through
`used_by`. **No cross-agent skill need surfaced in either design** — main-agent mediation
(option 3 above) remains sufficient in practice for this consumer, because the shared
infrastructure is a program on PATH, not a prompt to load.

Worth stating as the general shape rather than a coincidence: an infrastructure capability that
ships a deterministic tool exports it as a *process*, and a process boundary is a better
composition seam than a shared prompt — it is versioned, it has exit codes, and it cannot
quietly consume the caller's context window. The second evidence question (harness-native
skill-scoping across profiles) is still open. This narrows what build 3 needed; it does not
resolve the RFC, which **stays open**.

## Process

Deferred to its own session (deliberate — raised during the kb redesign, 2026-07-23, not solved there). Decide before build 4 if a build surfaces a real cross-agent need; otherwise decide by the last build. Build 3 has now been done twice without surfacing one. **Decided 2026-10-12**: the need surfaced in a dogfooded use-case capability (the Resolution section above); proposed, closing after the dogfood period, like RFC-005.
