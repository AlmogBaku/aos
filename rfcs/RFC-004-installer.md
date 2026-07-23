# RFC-004: Install bookkeeping — helper tool or prose all the way down?

**Status:** decided (2026-07-23) · **Decision:** no kit-level helper tool; capabilities ship their own deterministic tools

## Settled (not this RFC)

ARCHITECTURE §5.1–5.2 is firm: **the harness's own LLM installs capabilities**, guided by the capability's declarative manifest and a per-harness cheat-sheet. There is no installer program, no code adapters. §5.4 is also firm: every mutation is diff-previewed, recorded in `installs.lock.yaml`, backed up before upgrades, and auditable via `doctor`.

## Decision

**No kit-level helper tool — at least for now.** The deterministic-mechanics problem is real (prose-executed hashing, glob math, and table parsing are what LLMs fumble silently), but the right home for the answer is **per-capability tools**, not a kit binary:

- A capability whose skills contain deterministic checklists ships them as **one bundled tool** inside its entry skill's `scripts/` (ARCHITECTURE §2.4 "Capability tools"), run via the ecosystem's zero-install runner. The kb capability's `base` tool is the first instance: catalog, state, lint, search, grants lookup, sync — every [D] operation its skills would otherwise prose-execute.
- The boundary from the original recommendation is kept and generalized: *judgment in the LLM, mechanics in the tool* — a capability tool performs deterministic operations only, never calls an LLM, never invokes an agent, and communicates back through exit codes, stdout, and files.
- Install/upgrade bookkeeping itself (lockfile, hashes, backups) **stays prose for now** — the cheat-sheet playbook. It is exactly the kind of mechanics a tool should own, but no capability needs it machine-shared yet (rule-of-two); when a second harness's install flow visibly drifts the lockfile format, the bookkeeping verbs join a capability tool or this RFC reopens for a scoped `doctor` tool.

## Why not a kit-level tool

One kit binary would centralize what capabilities can ship independently, create a versioning coupling between the kit and every capability, and grow opinions (the failure mode the original recommendation warned about). Capability-shipped tools version with their capability, travel with its skills, and die with its removal.

## Consequences

- ARCHITECTURE §2.4 carries the capability-tool contract (this RFC's normative outcome); §8 lists it as a firm position.
- kb's `base` tool is the reference implementation; its verb set and test pattern (black-box subprocess, report-is-the-interface) are the template for future capability tools.
