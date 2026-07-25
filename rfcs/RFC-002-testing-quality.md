# RFC-002: Testing & merge quality

**Status:** open · **Decides:** how a capability proves it works before merge

## Question

What keeps the repo healthy instead of a graveyard? Capabilities are mostly prompts + conventions; classic unit tests cover little. The install transform is agentic (ARCHITECTURE §3.2), so "does it install" is itself a judgment call.

## Options

1. **Three tiers (recommended):**
   - **Tier 1 — deterministic CI (blocking):** manifest schema lint, Agent Skills SKILL.md frontmatter validation (including the spec's reserved words and the no-XML-tags rule), skill-identity checks (the computed installed name's format, cross-capability uniqueness, no redundant prefix, references by installed name — §2.1), progressive-disclosure checks (no reference chains, a Contents block past 100 lines), MOD.md-invariant check (no MOD.md in PRs), overlay-schema validation, dead-reference check.

**Open (2026-07-25):** the Agent Skills authoring guide's own testing checklist asks for **≥3 evaluations per skill** and a **Haiku/Sonnet/Opus matrix**. The kit has no equivalent — tier 0 is unit tests, tier 1 is lint, tier 2 is a single-model golden render. The eval loop currently arrives as *referenced knowledge* (Anthropic's `skill-creator`, installed by capability-lifecycle), not as kit machinery. Whether per-skill evals become a tier, and whether cross-model testing is a merge gate or advisory, is unresolved.
   - **Tier 2 — golden renders (blocking once adapters exist):** snapshot the install transform's output against fixture harnesses + a fixture MOD.md; PRs show the render diff. Agentic ≠ untestable: same inputs should produce *equivalent* artifacts, and a reviewer judges the diff.
   - **Tier 3 — scenario transcripts (non-blocking in v0.1):** a recorded end-to-end session (install → onboard → use) attached to the PR as evidence. Becomes blocking when tooling matures.
2. **Peer review only:** two approvals, no CI. Cheapest, decays fastest.
3. **Harness-in-a-box CI:** spin real harnesses in CI and run installs end-to-end. The right end state; far too heavy for v0.1.

## Recommendation

Option 1. Support-matrix honesty (ARCHITECTURE §5.3) does the rest: a capability claims only harnesses someone actually runs it on, with a named runner.

## Process

Auto-accept per RFC-003 window.
