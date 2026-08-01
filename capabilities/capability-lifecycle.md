# Capability: capability-lifecycle

**Tags:** infra · **Build order:** 2 (with kb) · **Seam it proves:** the lifecycle itself is a capability — day-N install/upgrade/remove/onboard/import/build/contribute/evolve live in the harness as skills, not in a repo file

> 📐 **Full design:** [design/install-flow.md](../design/install-flow.md) (the procedures its skills operationalize) · [RFC-004](../rfcs/RFC-004-installer.md) (the bookkeeping-tool decision whose reopen path this capability took).

## Scope

The whole life of a capability as **nine `main`-scoped skills** under `skill_prefix: capability-` (§2.2), ids action-oriented and bare because the prefix carries the family name (§2.1):

| Skill (installed name) | What it owns |
|---|---|
| `capability-lifecycle` | the entry skill: the map, the Experience rules, and the shared depth the others read — the install contract, the naming/identity rules, the overlay doctrine |
| `capability-install` | §5 install: manifest → deps → **name gate** → interview → render → STAGE→GATE→EXECUTE → link + record |
| `capability-upgrade` | pull upstream, fold drift into MOD.md, re-render upstream × MOD.md, git-diff gate, retire absorbed statements, walk absorbed capabilities |
| `capability-remove` | lockfile-driven exact removal; `MOD.md` always survives |
| `capability-onboard` | §3.2 the interview engine: a capability's `ONBOARDING.md` → the user's `MOD.md` (typed answers in frontmatter, prose nuance in the body, `secret: true` → store references). Re-runs ask only missing/`re_ask` questions; `--refresh` re-asks all and diffs first. **The only writer of `MOD.md`.** Also owns the global bootstrap interview — identity, timezone, working hours, sacred time, red lines |
| `capability-import` | §6 wrap → share: introspect → cluster → map → split → draft + GAP report. Read-only on the live harness |
| `capability-build` | §9 the MARS building-mode detector plus intake → research → design → approval → build. Output lands in the user's `personal/` root (§3.1); at completion it runs the §9 generality judgment and only then *offers* to contribute (niche → a soft "say *contribute it* anytime"; borderline → suggest a signal issue) |
| `capability-contribute` | the shipped source, for everyone: small tweaks land directly and transparently, major ones re-run the research/design/approval shape scaled down; drafts the upstream branch and opens the PR only on explicit confirm |
| `capability-evolve` | *your* install, through the overlay — and the overlay's exit side |

Plus the overlay mechanism (§3: interviews → MOD.md, the `{{mod}}` transform, MOD.md as the user's stated deltas with `capability-evolve` as its write path), the per-harness cheat-sheets (shipped in-capability at `harnesses/<harness-runtime>.md`, §5.2), the MARS mode-boundary block on the front agent's identity file (§9), and the `aos-cap` tool (§2.4: manifest parse/validate, **installed skill names + the collision gate**, the mechanical render, and the lockfile verbs — the lockfile is the tool's file; agents call verbs, never edit the YAML). `BOOTSTRAP.md` shrinks to a warm stub that inline-installs this capability (the only chicken-and-egg break) and hands over.

Boundaries the skills keep between themselves: `capability-evolve` changes *your install* through the overlay; `capability-contribute` changes the *shipped source* for everyone; `capability-build` makes something that does not exist yet. Evolve is the single front door for "change this" and routes — and the overlay has an exit side (§3.3): a generally-useful statement is promotable (signal-gated per §9's judgment, lightest rung first) and retires once an upgrade lands the upstream version covering it.

**Why one capability and not four.** `onboarding`, `importer`, and `capability-builder` shipped separately until the build phase showed they were carving one subject: the authoring skills share their invariant word for word (read-only on the live harness, write-only into a draft under `personal/capabilities/<id>/`, never install, never open the PR), and build's mechanism/nuance split is import's in reverse. §9 records the firm-position change — building mode stays a *mode* boundary, it just stops being a *package* boundary — with its cost stated plainly: BOOTSTRAP installs this capability for everyone, so the boundary now reaches consume-only users.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

- The proven funnel: real-Hermes e2e cycles (full install, day-N install, evolve, exact removal) driven by the pre-capability BOOTSTRAP — its §0 contract, interview mechanics, and no-cheat-sheet procedure are the extraction sources for `reference/contract.md`, `reference/naming.md`, `reference/overlay.md`, `reference/no-cheatsheet.md`.
- The four research-drafted cheat-sheets (hermes e2e-verified; nanoclaw v1+v2, openclaw, nanobot research-drafted).
- The interview UX: the "interview me, I hate blank pages" flow already proven in Almog's setup, plus the BOOTSTRAP interview of coleam00/second-brain-starter (but re-runnable, never self-deleting). Personalization is hardcoded in `state/SOUL.md` and persona files today — the biggest genuine gap in the live setup.
- kb's `base` tool packaging + black-box test pattern — the template `aos-cap` mirrors.
- Anthropic's `skill-creator` skill for generic skill craft — **referenced, never vendored** (Apache-2.0, kept current under `<home>/vendor/`): it owns drafting, description-trigger tuning, evals, packaging; `reference/naming.md` owns aos identity, and aos wins on names.

## Depends

`capabilities: []` · `host: {}` — but bootstrap itself requires `git` and **`uv`** (hard prerequisite: `uv` carries `aos-cap`; BOOTSTRAP step 0 offers the official installer and refuses to continue without it. kb's prose fallback for its own verbs is unaffected).

## Onboarding sketch

It ships `ONBOARDING.md` + `MOD.example.md`, but their subject is the **user**, not this capability's behaviour: the global bootstrap interview that writes the root `MOD.md` every other transform reads. Its own nine skills stay `{{mod}}`-slot-free, which is what keeps the bootstrap inline install purely mechanical.

## v0.1 acceptance

One uninterrupted sequence on a real harness: paste-block → welcome-and-explain before any action → prerequisites verified → the ten skills + `aos-cap` materialize (name gate → STAGE→GATE→EXECUTE, tool-recorded lockfile) → the global interview runs from `capability-onboard` → kb installs *through `capability-install`* → a **separate, fresh prompt** installs gtd-capture (proving day-N triggering with no BOOTSTRAP in context) → a planted name collision stops that install at the gate with nothing written → an evolve records a nuance in the capability's MOD.md and refreshes hashes (`aos-cap verify` clean) → removal via `capability-remove` walks the lockfile to a prestate-identical harness. Structural checks per the golden-render protocol (RFC-002).

## Note on build order

Sits at #2 with kb rather than at the end, where the original thirteen-step sequence put
it: built at the maintainer's direction after the first funnel slice proved the gap —
after bootstrap, nothing in the harness knew how to install. Everything after it installs
*through* it.
