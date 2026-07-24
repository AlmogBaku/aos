# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**`main` is the built kit; the spec lives on the `spec` branch.** The build phase's first slice is here — the Hermes cheat-sheet, the lint CI, and four committed capabilities: `kb` (infra, ships the `base` tool), `onboarding` (infra), `gtd-capture` (usecase, built on kb), `importer` (infra), and `capability-builder` (infra, the building-mode boundary; its ARCHITECTURE §9 lands with the same changeset). The spec docs (ARCHITECTURE.md, design/, capability one-pagers, RFCs, prior-art) are the reference-on-paper and live **only on the `spec` branch** — read them with `git show spec:<path>` or a `spec`-branch checkout/worktree; do not copy them back onto main. For a capability not yet built, its spec docs are the only source of truth. (`aos` is a placeholder name; RFC-001 picks the real one.)

The subject matter is a protocol: a curated set of *capabilities* that install into an existing agent harness (Hermes, NanoClaw, OpenClaw first; Claude Code, OpenCode later), personalize themselves via an onboarding interview, and survive upgrades. The kit is deliberately "protocol + implementations, no runtime".

## Commands

**`bash tools/check.sh` is the one local gate — run it before every commit.** It runs, in order, everything CI runs (`.github/workflows/ci.yml`):

- **Tier 0 — the `base` tool** (`capabilities/kb/tool`, a Python CLI; requires [`uv`](https://docs.astral.sh/uv/), skipped locally with a warning if absent): `uv run tests/tool/test_base.py` (black-box subprocess unit suite — the report text is the contract, no imports of tool internals) + lint the shipped example base (`tests/fixtures/example-base/` must pass `base lint` with zero criticals/findings).
- **Tier 1 — deterministic lint**: `node tools/lint/aos-lint.mjs` (~17 check families over the §2/§3/§5 contracts) + `node tools/lint/selftest/run.mjs` (every check must fire on a planted-violation fixture).
- **Tier 2 — golden structural checks**: `node tests/golden/check.mjs` (re-checks committed snapshots under `tests/golden/hermes/`).

Narrower invocations:

- **One base-tool test**: `uv run tests/tool/test_base.py BaseToolTest.test_capture_lands_pending_with_log_line`
- **Lint diff-aware (version-bump check)**: `node tools/lint/aos-lint.mjs --base origin/main` — the `version/bump` check only fires with `--base`, requiring a `CAPABILITY.md` version bump when a capability's files change.
- **Run the `base` tool ad hoc**: `uvx --from capabilities/kb/tool base --help` (verbs: `init adopt capture inbox state search links lint grants index sync verify import survey`).
- **The e2e (tier 2 live)** is a REAL install into a disposable `aos-test` Hermes profile — never simulated. Exact prompts + steps: `tests/golden/PROTOCOL.md`; then `node tests/golden/check.mjs --live full-install` and `node tests/golden/normalize.mjs`. See `docs/TESTING.md`.

## Document map

On the **`spec` branch** (authoritative for contracts; `git show spec:<path>`):

- **`ARCHITECTURE.md`** — the spec, and the only document that is normative. §2 capability package format, **§3 the overlay contract (declared inviolable)**, §4 KB registry/routing/authorization, §5 install via the harness LLM + cheat-sheets, §6 importer, §7 build order, **§8 the decision index**, Appendix B (risk register).
- **`rfcs/RFC-00N-*.md`** — the eight open decisions · **`capabilities/*.md`** — one-pagers (with each capability's v0.1 acceptance) · **`design/*.md`** — deep-dive exhibits (`capability-anatomy.md` is the worked example built capabilities mirror) · `prior-art.md`, `diagram.svg`.

On **main** (this branch — the build):

- **`capabilities/<id>/`** — built capability directories (§2.1 layout). Every capability mirrors the §2.5 anatomy: an **entry skill** named after itself (`skills/<id>/SKILL.md` — the runtime face; a short map) with on-demand depth in a sibling `reference/` **one level deep** (not the old `skills/<skill>/sections/`). `kb` additionally ships its `base` tool at `capabilities/kb/tool/` (a `uv`-installed Python CLI, the §2.4 deterministic executor — judgment-free by contract: no LLM, no agent, files + exit codes are the interface).
- **`harnesses/hermes/CHEATSHEET.md`** — the first per-harness knowledge artifact (§5.2's six sections).
- **`BOOTSTRAP.md`** (repo root) — the agent-facing install script the README paste-block points at; **`CONTRIBUTING.md`** (repo root) — the contributor guide.
- **`docs/`** — `CONCEPTS.md` (the mental model, explanatory — contracts live on the spec branch, never restated), `INSTALL.md` + `USAGE.md` (human-facing how-to guides), `TESTING.md` (how to run everything), `BUILD-GAPS.md` (**the spec-gap ledger — every artifact↔spec mismatch gets a row; artifact-side fixes land in the same main commit, spec-side fixes land on the `spec` branch and the row names them**), `DOGFOOD.md` (deferred live-dogfood checklist), `diagram.svg` (the architecture illustration, copied from the spec branch by explicit decision).
- **`tools/`** — the RFC-002 tier-1 lint (`lint/`, schema/contract validator with a planted-violation `selftest/` — useful for authoring any capability, not just testing) + `lib/` (shared code; `constants.mjs` is the single source of every schema vocabulary and the `KIT_NAME` placeholder, so the RFC-001 rename is a one-file sweep). `bash tools/check.sh` runs everything CI runs. **Run it before every commit.**
- **`tests/`** — `tool/test_base.py` (the tier-0 `base`-tool suite), fixtures (Dana Fixture persona + sentinels; `example-base/` is the golden `base lint`-clean tree), the golden-render machinery (`tests/golden/`: `check.mjs`/`normalize.mjs`/`prestate.sh` — test-only, so they live here rather than in `tools/` — plus snapshots under `tests/golden/hermes/`), and transcripts of real runs. The e2e is a REAL install into a disposable `aos-test` Hermes profile namespace — see `tests/golden/PROTOCOL.md`; never simulate the harness, and never touch `~/.hermes` outside `aos-*` profiles or `~/ai-kb` at all.

## Firm position vs. open RFC — check before changing any decision

ARCHITECTURE §8 splits every decision into two tables:

- **Firm positions** carry a rationale and a section number. They can change, but via an issue against that specific section *with a counter-proposal* — not by quietly rewording the spec.
- **Open RFCs** must not be resolved inside ARCHITECTURE or a capability page. RFC-006 owns the multi-KB routing/authorization behavior and RFC-007 the permission-gate vocabulary; the `kb` and `permission-gate` pages proceed with their build plans but explicitly defer the contested behavior, and edits should preserve that split.

## Normative rules that are easy to break while editing

- **The overlay family** — every `MOD.md` (global + per-capability) and `kb-registry.yaml` — is user-owned. Upstream never ships, writes, or merges those paths; do not create them in this repo. `.aos/` is machine-local state and gitignored. (ARCHITECTURE §3.1; `.gitignore` explains why the overlay family itself is deliberately *not* ignored — that's RFC-005.)
- **Rule of two** — a manifest/schema field only exists once two in-repo capabilities need it machine-read; until then it stays prose. §2.2 lists what was deliberately left out (`provides` graph, hooks vocabulary, per-capability grants, model/cost hints); don't "helpfully" add them.
- **No program anywhere** — `aos import` / `install` / `update` are conversational actions the harness agent performs, never a CLI. Per-harness support is a `CHEATSHEET.md` (knowledge), never adapter code. Capability-shipped software is standalone behind a process boundary, reached by a thin per-harness shim.
- **Skill scoping** — every skill declares `used_by`; agents only load skills declared for them. There is no cross-*capability* skill-sharing vocabulary (`used_by` can't name another capability's agent — that's open RFC-009); one capability composes with another only through the shared `main` agent or a tool on PATH (how gtd-capture reaches kb — via the `base` command, never a foreign skill).
- **Entry-skill anatomy (§2.5)** — every capability ships `skills/<id>/SKILL.md` (lint-enforced, `structure/entry-skill`), with depth in a sibling `reference/` **one level deep** — no reference chains. `CAPABILITY.md` is the *installer's briefing* (consumed at install, never loaded at runtime); the entry skill is the *runtime face*. Don't reintroduce the retired `skills/<skill>/sections/` layout.
- **KB safety** — `audience: shared` KBs never accept LLM-routed writes (rule-matched, explicitly tagged, or human-approved only); capture latency is sacred, so routing is never a synchronous prompt.
- **Single-owner rule** — each `schedules[]` entry runs in exactly one harness at a time.

## Build phase (this is what the new session is for)

The build phase turns the spec into the artifacts it describes. The spec docs become the **reference-on-paper**: build against them, and treat `design/capability-anatomy.md` as the worked example every capability directory should mirror.

- **Order is fixed — follow ARCHITECTURE §7.** Build `kb` and `onboarding` first (the installer needs both), then `gtd-capture`, then the `importer`, etc. Each step exists to prove exactly one seam; don't build ahead of it. **Hermes is the first harness**, so the first artifact that doesn't exist yet is `harnesses/hermes/CHEATSHEET.md` (its required sections are in ARCHITECTURE §5.2).
- **What "build a capability" means, concretely:** create the directory exactly per ARCHITECTURE §2.1/§2.5 — `CAPABILITY.md` (typed frontmatter + prose *installer's briefing*), the `skills/<id>/` entry skill plus any focused skills (valid Agent Skills folders — the portable core; agent prompt bodies co-locate under `agents/<name>/`), `agents/*.agent.yaml` if it needs its own agent, `ONBOARDING.md` (frontmatter questions + interview script) and `MOD.example.md` (the shipped seed) — required as a pair, or neither (importer ships neither), plus `kb/` and `adapters/<harness>/` as needed. The `kb` capability additionally ships its `base` tool (`capabilities/kb/tool/`) and the init templates under `skills/init/templates/` (BASE.yaml, AGENTS.md w/ grants seed, state.yaml…) — design in `design/kb-methodology.md`; there is no methodology subdirectory (the seam was dissolved; kb IS the methodology).
- **Self-containment is a hard guardrail — this repo is public.** Reference capabilities are *extracted from* a live private setup (a production KB, a Hermes install), but nothing personal may land in a committed file: no real names/companies/relationships, no secrets or tokens, no actual KB content. `ONBOARDING.md` ships *questions*; `MOD.example.md` ships *placeholder* answers, never anyone's real ones. Extraction = lift the mechanism, genericize the content. When in doubt, redact.
- **When building reveals a spec gap, fix the spec — don't diverge.** The method is "build reveals what to spec." If a contract doesn't fit reality, update ARCHITECTURE **on the `spec` branch** via the firm-position discipline (or open/adjust an RFC there); rule-of-two still governs any new field. A capability silently inconsistent with a contract is a bug in one or the other — never something to leave standing.
- **Verifying with no runtime:** "does it work" = can the harness LLM, given only the capability + the harness `CHEATSHEET.md` + a fixture `MOD.example.md`, produce a correct install? That is the golden-render test (RFC-002 tier 2); dogfood it on Hermes for real. Tier-1 lint (schema / frontmatter / `used_by` / overlay-family checks) is the first CI to stand up (RFC-002).

## Conventions when adding documents

- Match the existing section skeleton for the family you're adding to (capability one-pager, RFC, design deep-dive). New RFCs take the next `rfcs/RFC-00N-<slug>.md` number.
- Cross-links are relative; diagrams are inline mermaid inside the markdown. **Every mermaid block must parse** — the gotcha that bit us: a `;` inside a *sequence-diagram* message is a statement separator and breaks rendering (use `—` or `,`). It's fine inside a quoted flowchart label.
- Adding or removing a capability or RFC means updating the tables that index them: ARCHITECTURE §7 (build order), §8 (both decision tables), Appendix A/B where relevant, and the README reading list. A new design deep-dive should be linked from both ARCHITECTURE and the capability page it serves.
- ARCHITECTURE's own bar (risk #5): a contract no reference capability exercises gets cut. Prefer sharpening an existing section over adding a new one.
