# Capability: kb

**Tags:** infra · **Build order:** 1 · **Seam it proves:** the whole neutral contract + first cheat-sheet

> 📐 **Full design:** the base engine (store · curation · state — the base tree, `.kb/base.yml`, page schema, current-truth doctrine, curation loop, state mechanics, recall, the `base` tool) is in [design/kb-methodology.md](../design/kb-methodology.md); the routing + access-control layer is in [design/kb-authorization.md](../design/kb-authorization.md).
>
> ⚠️ **Contested core:** the multi-base routing + authorization model is under active decision in [RFC-006](../rfcs/RFC-006-multi-kb-routing.md). The build proceeds regardless; the router's final behavior follows the RFC.

## Scope

The knowledge-base infrastructure capability. A KB instance is a **base** (`base == repo`); the capability ships the multi-base registry (`kb-registry.yaml`), the routing skill (rules → confidence-gated LLM → default pending), the authorization rules (shared bases never accept LLM-routed writes), and the **base engine** — three pillars (ARCHITECTURE §4.4): **store** (immutable raw + current-truth wiki pages under a per-base `BASE.yaml` schema), **curation** (instant mechanical capture → default-empty promotion → lint → answers filed back; one Archiver agent across all bases), and **state** (one capped rolling `state.yaml` attention window per base, composed at cold start). Six skills — ids `kb` (entry), `route`, `recall`, `init`, `adopt`, `import`; kb declares no `skill_prefix`, so they install as `kb`, `kb-route`, `kb-recall`, `kb-init`, `kb-adopt`, `kb-import` (§2.1 — the ids are capability-local, the installed names are what carry meaning in a crowded harness). `import` is interactive bulk import of existing KBs — the ~/ai-kb migration path; engine design §6.7) — and one capability-shipped deterministic tool (`base`, bundled in the entry skill: capture/inbox/state/search/links/lint/grants/index/sync; RFC-004's outcome). The kb capability *is* the methodology (Karpathy-LLM-wiki lineage, extended); no pluggable seam ships in v0.1. `base init` interviews, writes BASE.yaml, and scaffolds; `base adopt` registers an existing tree and lint-reports divergence without rewriting.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

- Methodology, production-proven since June 2026: the live KB's 3-layer contract, zone table, write rules, sync discipline — since redesigned into the base engine (BASE.yaml + AGENTS.md; SCHEMA.md and the state/ directory are superseded per the engine design).
- Operational scaffolding: the review-queue and lint-report conventions (now one `.kb/pending/` queue and stdout), and `_raw/` sha256 dedup.
- Sync: the 5-min rebase-only cron (now `kb sync` on an `exec:` schedule — no LLM in the loop).
- Archiver: a live Hermes profile with the nightly drain + weekly lint.

## Depends

`host: cron: preferred` (promote + lint agent schedules, sync exec schedule; degraded: manual). No capability deps — this is the root molecule.

## Onboarding sketch

Which bases exist / create how many; per base: theme (drives the init interview's zone/type design written into `.kb/base.yml`), path, remote, audience (shared/private), purpose (one paragraph — doubles as the router's and recall's rubric), channel bindings; default base.

## v0.1 acceptance

The four-tier ladder passes in one uninterrupted sequence: tool unit tests (incl. the shipped example base passing `kb lint` clean in CI) → kit lint → golden renders (install, init-interview, adopt-divergence) → the real-Hermes e2e ("a week in the life": install, init two bases, capture burst incl. duplicate + injection sentinel, promote with default-empty visible, recall with citations + gap admission, state cap + staleness mechanics, authz leakage probes, exec-sync with a manufactured conflict and zero agent invocations, upgrade + removal). `kb adopt` on a production-shaped fixture runs clean; import survey on an old-layout fixture detects the shape read-only (source byte-identical — the skill's invariant); the routing replay bar stays RFC-006's (<5% misroute, Appendix B #2).
