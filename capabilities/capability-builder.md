# Capability: capability-builder

**Tags:** infra · **Build order:** 12 (appended — see note) · **Seam it proves:** a structural, prompt-enforced mode boundary between operating and building, with an approval gate before anything durable gets written

## Scope

The building-mode boundary from MARS (the Mode-Aware Runtime System pattern — ARCHITECTURE §9 defines it), made real. A **conversational**, `main`-scoped detector: when a request drifts from a one-off task into something that would create persistent, unattended state (a skill, a schedule, an agent, a standing automation), it interrupts — *"should we plan this methodically?"* — instead of letting the harness silently improvise the underspecified parts. If the user agrees, `main` follows a scoped procedure on itself (intake → research via subagents → a single design proposal → **explicit user approval** → build) rather than switching to a separate materialized agent — no harness in scope here exposes a live conversation-handoff primitive, and prompt-enforced mode boundaries are a known-working shape for exactly this problem elsewhere in the field. Output is a capability package written into the user's clone, same invariant as the importer: never installs, never opens a PR. Also evolves capabilities that already exist — small feedback lands directly and transparently; feedback that changes what a capability owns or does re-runs the research/design/approval shape, scaled down.

## What exists today

Nothing to wrap — this is greenfield, not extracted from a live setup. The shape converges independently with plan-and-execute agent architectures, coding-agent plan modes, and human-in-the-loop approval-gate frameworks elsewhere in the field; the capability's own reference docs carry the calibration that converges on (gate by persistence/blast-radius, not by word choice, and never by gating everything).

## Depends

`capabilities: [onboarding]` (the capability packages it authors ship their own `ONBOARDING.md`, following onboarding's schema conventions, same as the importer's drafts do).

## Onboarding sketch

None for v0.1 — mirrors the importer, the only other capability that ships neither `ONBOARDING.md` nor `MOD.example.md`. A later version could add a single interrupt-sensitivity dial; deferred rather than speculatively added now.

## v0.1 acceptance

The detector fires on use-case-shaped requests and stays silent on task-shaped ones across a fixture transcript sweep; a decline is respected without re-prompting on the same request; a full intake → research → design → approval → build run produces a lint-clean capability package, with nothing written before approval; small evolve-capability feedback applies without a gate and major feedback re-triggers the scaled procedure. Structural checks per the golden-render protocol (RFC-002).

## Note on build order

Not one of the original eleven — added after v0.1's initial reference set was speced, at the maintainer's direction (see the built artifact's `docs/BUILD-GAPS.md` row on `main`). Its natural conceptual slot is beside the importer (build 4): both are "how a capability comes into existence" — idea-to-package here, existing-stuff-to-package there. Appended as build 12 instead of renumbering an already-firm order; revisit if the group wants it moved.
