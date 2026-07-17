# Capability: importer

**Tags:** infra · **Build order:** 4 · **Seam it proves:** cheat-sheet-guided introspection + the generic/personal split; the format's stress test

## Scope

A **conversational** capability, not a CLI. You ask your harness agent, in plain language — *"import my trainer use-case and its agent into the aos kit"* — and the importer skill drives the agent (which already knows its own setup) through: inventory its own skills/crons/profiles/workspace files (guided by the cheat-sheet's introspection section) → cluster artifacts into candidate use cases → map each to a package primitive → split generic mechanism (package skeleton) from personal nuance (draft `MOD.md`) → emit `capabilities/<id>-draft/` + `GAP.md` (hardcoded paths, harness-only APIs, flagged inline secrets — never copied). It only *reads* the harness and writes a draft — never installs, never opens PRs. This is *more* agentic than install (pure judgment, no live mutation), which is exactly why it's a skill and not code.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

The fixtures, not the tool: Hermes trip-planning (travel skill + `ops/trips/` conventions) and the time-blocking fragments (gog calendar reads + SOUL.md scheduling rules + cron entries). The tool itself is new.

## Depends

`capabilities: [onboarding]` (drafting MOD.md uses its schema conventions) · the source harness's cheat-sheet (introspection section).

## Onboarding sketch

None — it's a contributor tool, invoked by asking. It reads which use case you name and infers the rest from the harness.

## v0.1 acceptance

The two fixtures import to drafts a human can polish into merge-ready capabilities in under an hour each; the **personal-trainer loop**: a collaborator imports their Hermes personal trainer, the draft PRs cleanly, a second user installs and onboards it (ARCHITECTURE §1.1). GAP.md findings convert into spec fixes.
