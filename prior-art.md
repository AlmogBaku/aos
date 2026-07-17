# Prior art: where this kit sits

*Research snapshot, July 2026. The two poles that matter, and the square nobody occupies.*

## gstack (Garry Tan) — closest on architecture & distribution

[github.com/garrytan/gstack](https://github.com/garrytan/gstack) · MIT · launched 2026-03-12 · ~122k stars. "23 opinionated tools" (really ~50 skills + TS tooling) turning Claude Code into a virtual dev team, multi-host via one declarative `hosts/*.ts` file per agent (10 hosts), paste-one-line install, state segregated in `~/.gstack/` (taste profiles, learnings, config) that updates never touch.

**Same shape as us:** Agent Skills superset with extended frontmatter · one curated repo · per-harness one-file translation · state outside the package · paste-to-install · silent update checks. Its OpenClaw path even validates our §5 exactly: paste a natural-language instruction, *the agent's own LLM performs the install*.

**Where it breaks — and where our thesis lives:** no content personalization. Adapting a persona's text means *fork the repo and lose upgrades* (the community's own recommended workaround); its harshest reviewer kept 6 of 35 commands — unadapted opinionated packs shed most of their surface. No onboarding interview (it assumes you are Garry Tan), no schedules at all, contribution requires TypeScript+Bun. Our MOD.md overlay + interview + LLM-merge-guided-by-overlay is precisely the layer gstack conspicuously lacks at 122k stars.

**What we steal:** paste-to-install as the whole funnel · `sections/*.md` decomposition + per-skill semver (makes LLM merges per-section, not per-monolith) · one-file-per-harness as a first-class contribution path (`docs/ADDING_A_HOST.md` equivalent) · a countable noun and a named loop (marketing discipline) · state-never-touched-by-updates as the floor under the overlay.

*(Amusing footnote: gstack's own README demo is the user building "a personal chief-of-staff AI" — our domain is their example use case.)*

## PAI / LifeOS (Daniel Miessler) — closest on domain

Personal life-OS on Claude Code: 45 skills, 171 workflows, `/interview` onboarding, release system. Right domain, wrong architecture for our problems: single-harness by construction, personalization by forking ("template, don't fork" is the community norm — i.e., no upstream story), no overlay, no cross-harness anything.

## The open square

| | dev-team domain | life-ops domain |
|---|---|---|
| **fork-to-personalize** | gstack | PAI/LifeOS |
| **overlay-survives-upgrades** | — | **this kit** |

Neither pole has: content-personalization overlay · onboarding that writes it · cross-harness LLM install · schedules as a first-class primitive · multi-KB with authorization. gstack proves the demand for curated capability packs; PAI proves the appetite for the life-ops domain; the defensible novelty here is **personalization that survives upgrades, across harnesses**.

Position in one line: *gstack's distribution architecture, applied to chief-of-staff life-ops, with the personalization layer gstack doesn't have.*
