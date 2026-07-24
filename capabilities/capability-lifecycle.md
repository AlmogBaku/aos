# Capability: capability-lifecycle

**Tags:** infra · **Build order:** 13 · **Seam it proves:** the lifecycle itself is a capability — day-N install/upgrade/remove/evolve live in the harness as skills, not in a repo file

> 📐 **Full design:** [design/install-flow.md](../design/install-flow.md) (the procedures its skills operationalize) · [RFC-004](../rfcs/RFC-004-installer.md) (the bookkeeping-tool decision whose reopen path this capability took).

**Build-order note:** appended (like capability-builder, build 12) rather than resequenced next to kb/onboarding where it conceptually belongs — it was built at the maintainer's direction after the first funnel slice proved the gap: after bootstrap, nothing in the harness knew how to install.

## Scope

The install/upgrade/remove/evolve procedures as five `main`-scoped skills (`capability-lifecycle` entry + `capability-installer`, `capability-upgrader`, `capability-remover`, `capability-evolver` — ids self-descriptive out of context, §2.5), the overlay mechanism (§3: interviews → MOD.md, the {{mod}} transform, MOD.md-as-ledger with `capability-evolver` as its write path), the per-harness cheat-sheets (shipped in-capability at `harnesses/<harness-runtime>.md`, §5.2), and the `aos-lock` bookkeeping tool (§2.4 capability tool: manifest parse/validate + lockfile init/record/verify/show/list/remove — the lockfile is the tool's file; agents call verbs, never edit the YAML). `BOOTSTRAP.md` shrinks to a warm stub that inline-installs this capability (the only chicken-and-egg break) and hands over.

Boundary: `capability-evolver` changes *your install* through the ledger; changing the *shipped source* for everyone is capability-builder's `capability-source-evolver` (§9 building mode). The evolver is the single front door and routes.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

- The proven funnel: two real-Hermes e2e cycles (full install + exact removal) driven by the pre-capability BOOTSTRAP — its §0 contract, interview mechanics, and no-cheat-sheet procedure are the extraction sources for `reference/contract.md`, `reference/overlay.md`, `reference/no-cheatsheet.md`.
- The four research-drafted cheat-sheets (hermes e2e-verified; nanoclaw v1+v2, openclaw, nanobot research-drafted).
- kb's `base` tool packaging + black-box test pattern — the template `aos-lock` mirrors.

## Depends

`capabilities: []` · `host: {}` — but bootstrap itself requires `git` and **`uv`** (hard prerequisite: `uv` carries `aos-lock`; BOOTSTRAP step 0 offers the official installer and refuses to continue without it. kb's prose fallback for its own verbs is unaffected).

## Onboarding sketch

None by design — the lifecycle has no personalization; it ships neither `ONBOARDING.md` nor `MOD.example.md` (presence-paired rule, like importer). Its skills are `{{mod}}`-slot-free so the bootstrap inline install is purely mechanical.

## v0.1 acceptance

One uninterrupted sequence on a real harness: paste-block → welcome-and-explain before any action → prerequisites verified → the five skills + `aos-lock` materialize (STAGE→GATE→EXECUTE, tool-recorded lockfile) → onboarding and kb install *through `capability-installer`* → a **separate, fresh prompt** installs gtd-capture (proving day-N triggering with no BOOTSTRAP in context) → an evolve records a nuance in the capability's MOD.md and refreshes hashes (`aos-lock verify` clean) → removal via `capability-remover` walks the lockfile to a prestate-identical harness. Structural checks per the golden-render protocol (RFC-002).
