# Concepts — the mental model

This page *explains*; it never *specifies*. Every contract mentioned here is normative
only in [ARCHITECTURE.md on the `spec`
branch](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md) — section links
below. If this page and the spec ever disagree, the spec wins (and that's a bug worth a
[BUILD-GAPS](BUILD-GAPS.md) row).

## The big picture

![aos architecture diagram](diagram.svg)

The layering borrows Brad Frost's atomic design
([§1.2](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#12-mental-model-atomic-design)):
**skills** are the atoms, **infra capabilities** (kb, onboarding) the molecules,
**use-case capabilities** (gtd-capture) the organisms. The kit ships **templates** —
generic structure, personalization slots empty. Your harness runs **pages** — the same
capability instantiated with *your* answers. The transform between template and page is
where the whole product lives.

## Capability

*A distro package for your agent* ([§2](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#2-the-capability-package)).
Installing one does many things — places skills, creates an agent, registers schedules,
sometimes installs a tool — and, like a good package, it **declares** all of it so the
installer can perform, record, and reverse it.

A capability is a directory composing five building blocks
([§2.5](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#25-the-capability-lifecycle-briefing-then-building-blocks)):

| Block | What it is | Shipped as |
|---|---|---|
| Skills | knowledge agents load on demand | `skills/<skill>/SKILL.md` — portable [Agent Skills](https://agentskills.io) folders |
| Agents | personas that run scheduled/delegated work | `agents/<name>.agent.yaml` + prompt bodies in `agents/<name>/` |
| Tools | deterministic executables (no LLM inside) | e.g. [`capabilities/kb/tool/`](../capabilities/kb/tool/) |
| Crons | schedules, agent-type or script-direct | `schedules[]` in the manifest |
| Patches | harness modifications, when unavoidable | `adapters/<harness>/` |

Two files have special roles:

- **`CAPABILITY.md` is the installer's briefing** — typed frontmatter (machine-checked)
  plus prose the installing LLM reads for judgment ("create the drainer *before* its
  schedule", "this must run before kb's promote"). Consumed at install, never loaded at
  runtime.
- **The entry skill is the runtime face** — every capability ships one skill named after
  itself (`skills/<id>/SKILL.md`): a short map of where things live and which skill/verb
  does which job, with depth one `reference/` hop away. It's the thing an agent can
  always "hold" to understand the capability.

## The overlay — why upgrades can't eat your personalization

The one **inviolable** contract
([§3](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#3-overlay--onboarding--the-inviolable-contract)).
Your answers, nuances, and red lines live in `MOD.md` files (one global, one per
capability) plus `kb-registry.yaml` — together, the **overlay family**. Three rules make
them safe:

1. **Upstream never ships them.** The kit ships `MOD.example.md` seeds; your real
   `MOD.md` is written only by the onboarding interview, in your clone.
2. **Upstream never writes them.** `git pull` cannot touch a path it doesn't contain.
3. **Upgrades merge templates *under* your overlay** — new capability version × your
   current install × your MOD.md, diff shown before anything lands.

Hand-editing installed artifacts is normal and expected; the agent captures your edits
back into MOD.md when it notices them (the round-trip,
[§3.3](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#33-round-trip-edits-flow-back-to-modmd)).

## Onboarding — typed questions, one interview

Every capability may ship an `ONBOARDING.md`: typed questions in frontmatter (`string`,
`enum`, `path`, …, plus `secret: true` for values that go to the harness's secret store,
never into files), a conversational script in the body. The onboarding capability runs
it and writes your MOD.md. Re-runs only ask what's missing; `--refresh` re-asks
everything and shows the diff first.

## Knowledge bases — bases, routing, and why shared KBs are special

([§4](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#4-knowledge-bases-registry-routing-authorization))
A KB instance is a **base** (one git repo). You may have several — personal, a shared
work KB your colleagues pull — all registered in your user-owned `kb-registry.yaml`.

- **Routing is rules first.** Channel rules, explicit tags (`work: …`), and keyword
  rules decide deterministically; an LLM is consulted only above a confidence bar, and
  **never for a shared base** — a repo other people pull never accepts LLM-guessed
  writes. Capture latency is sacred: routing never blocks a capture on a question.
- **The base engine** ([§4.4](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#44-the-base-engine-store-curation-state)):
  immutable `raw/` captures + current-truth wiki pages; a skeptical nightly promotion
  (most captures aren't knowledge — default is empty); one capped `state.yaml`
  attention window per base.
- **The `base` tool** is the deterministic executor for all of it — capture, inbox,
  search, lint, sync, grants — files and exit codes, no LLM, no agent. Agents use it;
  they don't reimplement it.

## Install — the LLM is the installer

([§5](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#5-installation-the-harness-installs-the-batteries))
There is no installer program. Your harness's own agent reads
[`BOOTSTRAP.md`](../BOOTSTRAP.md), its harness's cheat-sheet, and each capability's
briefing, then materializes everything itself. Three mechanisms keep that honest:

- **Cheat-sheets, not adapters.** Per-harness support is one `CHEATSHEET.md` teaching
  the mapping (agent → Hermes profile, schedule → `hermes cron create`, secret →
  `.env`). Knowledge, not glue code — a new harness costs one document.
- **The diff gate.** Every write is shown to you in full before it lands. Never
  optional.
- **The lockfile.** Everything materialized is recorded in `.aos/installs.lock.yaml`
  (paths, hashes, owned schedule ids). Removal walks it backwards; no record, no
  artifact.

If a host feature is missing (no cron, no `uv`), the capability **degrades, declared**:
schedules become invocable run-cards, tools fall back to prose procedures — each
capability names its degraded modes up front.

## How decisions evolve

([§8](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#8-decision-index))
Every design decision is either a **firm position** (has a rationale and a section
number; challenge it with an issue *plus a counter-proposal*) or an **open RFC** (the
eight contested cores — naming, multi-KB routing, permission vocabulary, …). Building
against the current text is always allowed; resolving an RFC quietly inside a doc never
is. When building reveals the spec is wrong, the spec gets fixed — the
[BUILD-GAPS ledger](BUILD-GAPS.md) is the audit trail of every such fix.

## Glossary

| Term | Meaning |
|---|---|
| **harness** | The agent product you already run (Hermes, NanoClaw, OpenClaw, …) |
| **capability** | An installable directory of skills/agents/tools/crons/patches |
| **entry skill** | `skills/<id>/` — the capability's runtime face and map |
| **overlay** | Your `MOD.md` files + `kb-registry.yaml`; user-owned, never shipped |
| **base** | One KB instance == one git repo, registered in `kb-registry.yaml` |
| **materialize** | The installer writing a capability's artifacts into your harness |
| **cheat-sheet** | Per-harness knowledge doc the installing LLM follows |
| **lockfile** | `.aos/installs.lock.yaml` — the honest record of what was installed |
| **diff gate** | You see every write before it happens; never optional |
| **degraded mode** | A capability's declared behavior when a host feature is absent |
