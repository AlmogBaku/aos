# Capability: kb

**Tags:** infra · **Build order:** 1 · **Seam it proves:** the whole neutral contract + first cheat-sheet

> 📐 **Full design:** the knowledge model (3 layers, schema, growth stages, synthesis, retrieval) is in [design/kb-methodology.md](../design/kb-methodology.md); the routing + access-control layer is in [design/kb-authorization.md](../design/kb-authorization.md).
>
> ⚠️ **Contested core:** the multi-KB routing + authorization model is under active decision in [RFC-006](../rfcs/RFC-006-multi-kb-routing.md). The extraction plan below proceeds regardless; the router's final behavior follows the RFC.

## Scope

The knowledge-base infrastructure capability: multi-KB registry (`kb-registry.yaml`), the routing skill (rules → confidence-gated LLM → default inbox), the authorization rules (shared KBs never accept LLM-routed writes), and one shipped methodology — `karpathy-llm-wiki` — behind the pluggable methodology seam. The methodology is explicitly two pillars (ARCHITECTURE §4.4): **the Karpathy KB methodology** (immutable raw → synthesized wiki with wikilinks) **plus a rolling-window current-state mechanism** (`state/` — frequently rewritten "what's going on right now", so any agent can cold-start into current reality without replaying history). Ships the Archiver agent spec plus sync/lint/promotion schedules. `kb init` creates and registers; `kb adopt` registers an existing KB and lint-reports divergence without rewriting.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

- Methodology, fully specified and production-proven: `~/ai-kb/AGENTS.md` (3 layers, maintainer-zone table, write rules, sync discipline), `~/ai-kb/SCHEMA.md` (frontmatter, wikilinks, growth stages, tag taxonomy).
- Operational scaffolding: `_ops/` lint reports + review queues, append-only `log.md`, `raw/` sha256 dedup.
- Sync: `_ops/anakin-scripts/ai-kb-sync.sh` (5-min rebase-only cron).
- Archiver: a live Hermes profile with the nightly drain + weekly lint.

## Depends

`host: cron: preferred` (sync + lint schedules; degraded: manual). No capability deps — this is the root molecule.

## Onboarding sketch

Which KBs exist / create how many; per KB: path, remote, audience (shared/private), purpose (one paragraph — doubles as the router's rubric), channel bindings; default KB.

## v0.1 acceptance

`kb adopt` on an existing production KB runs clean; routing replay on two weeks of real captures stays under the 5% misroute bar (Appendix B #2).
