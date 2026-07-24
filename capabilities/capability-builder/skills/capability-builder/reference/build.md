# Stage 4 — Build

Only after Design is approved. Materialize into `capabilities/<id>/` in the user's
clone, following the package layout every other capability here uses: `CAPABILITY.md`,
`README.md`, `skills/<id>/SKILL.md` (the entry skill) plus any further `skills/`,
`agents/*.agent.yaml` only if it needs its own agent, `ONBOARDING.md` +
`MOD.example.md` only as a pair, `kb/` only if it touches a KB.

**Split mechanism from nuance — same discipline as the importer, in reverse.**
Everything personal Intake captured (names, channels, hours, preferences) goes into
the package's `ONBOARDING.md` as *questions*, and into the user's own
`capabilities/<id>/MOD.md` as their answers (overlay family — theirs, never shipped,
never in a PR). Shippable files get the generic mechanism plus `{{mod: …}}` slots
where nuance fills in; `MOD.example.md` gets invented placeholder answers, zero
personal data. No real name, channel id, or personal detail may land in any file the
package would ship.

**Never installs, never opens a PR** — same invariant as `importer`. The output is a
capability package sitting in the clone; installing it into the harness is the
already-specified install flow, a separate step.

Before calling it done: run the repo's tier-1 lint if `tools/` exists, and show the
user the full file tree plus a one-line summary of each new file.
