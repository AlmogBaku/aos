# Stage 4 — Build

Only after Design is approved. Materialize into
`<home>/personal/capabilities/<id>/` — the user's private repo, where their
capabilities live until (and unless) they graduate — following the package layout
every shipped capability uses: `CAPABILITY.md`, `README.md`, `skills/<id>/SKILL.md`
(the entry skill) plus any further `skills/`, `agents/*.agent.yaml` only if it needs
its own agent, `ONBOARDING.md` + `MOD.example.md` only as a pair, `kb/` only if it
touches a KB. The persist hook commits it (dated message).

**Split mechanism from nuance — same discipline as the importer, in reverse.**
Everything personal Intake captured (names, channels, hours, preferences) goes into
the package's `ONBOARDING.md` as *questions*, and into the user's own
`personal/capabilities/<id>/MOD.md` as their answers (overlay family — theirs, never
shipped, never in a PR). Shippable files get the generic mechanism plus `{{mod: …}}`
slots where nuance fills in; `MOD.example.md` gets invented placeholder answers, zero
personal data. No real name, channel id, or personal detail may land in any file the
package would ship.

**Never installs, never opens a PR** — same invariant as `importer`. The output is a
capability package sitting in `personal/`; installing it into the harness is the
already-specified install flow, a separate step.

Before calling it done: run the kit linter
(`node <home>/upstream/tools/lint/aos-lint.mjs`) — the new package must add zero
errors — and show the user the full file tree plus a one-line summary of each new file.

**Then, the contribute question — judgment-gated, never reflexive.** Run the
generality judgment (capability-lifecycle's overlay reference, "Promote and retire":
stranger test, dependency test, coherence test, the maintenance-willingness question,
the ledger search):

- **Clearly generally useful** → ask, once: *"Want to contribute this?"* Yes →
  duplicate the package onto a branch in `<home>/upstream`, run the self-containment
  scrub again on the copy, and continue per the `capability-source-evolver` skill's
  contribute reference — the PR opens only on the user's explicit confirm.
- **Clearly niche** (their org's CRM, their home server) → no prompt; one soft line:
  *"kept in personal/ — say 'contribute it' anytime."*
- **Borderline** → suggest a `promotion-signal` issue instead ("would others want
  X?") — filed only on explicit yes.
