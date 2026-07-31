# Stage 4 — Build

Only after Design is approved. Materialize into
`<home>/personal/capabilities/<id>/` — the user's private repo, where their
capabilities live until (and unless) they graduate — following the package layout
every shipped capability uses: `CAPABILITY.md`, `README.md`, `skills/<id>/SKILL.md`
(the entry skill) plus any further `skills/`, `agents/*.agent.yaml` only if it needs
its own agent, `ONBOARDING.md` + `MOD.example.md` only as a pair, `kb/` only if it
touches a KB. The persist hook commits it (dated message).

**Split mechanism from nuance — same discipline as {{skill: import}}, in reverse.**
Everything personal Intake captured (names, channels, hours, preferences) goes into
the package's `ONBOARDING.md` as *questions*, and into the user's own
`personal/capabilities/<id>/MOD.md` as their answers (overlay family — theirs, never
shipped, never in a PR). Shippable files get the generic mechanism plus `{{mod: …}}`
slots where nuance fills in; `MOD.example.md` gets invented placeholder answers, zero
personal data. No real name, channel id, or personal detail may land in any file the
package would ship.

**Never installs, never opens a PR** — same invariant as {{skill: import}}. The output is a
capability package sitting in `personal/`; installing it into the harness is the
already-specified install flow, a separate step.

Follow `capability-lifecycle`'s `reference/naming.md` for both halves of authoring: name
every skill action-oriented and bare (the prefix is applied at install), and place
knowledge where it will still resolve once installed — only the skill's own folder travels,
so depth goes in its `reference/`, another skill's knowledge is reached by naming that
skill, and anything in the household is written from a root. Run the uniqueness gate as the **first** thing after
`CAPABILITY.md` and before any skill directory: `aos-cap --home <home> skills <package-dir>
--check --harness-skills <the harness's skills dir(s)>`. The verb reads the manifest, so it
cannot run against an empty directory — writing the manifest first is the ordering, and it is
still before anything a collision would waste. Exit 17 means the name is taken; rename in the
package, never at install time.
For the skill's own craft — drafting, description triggering, evals — use the
`skill-creator` skill if it is installed; the aos rules above still win on names.

Before calling it done: run the **{{skill: review}} skill** over what you built. The linter
below validates schema — frontmatter, `used_by`, reference depth — and structurally cannot
check whether the prose you wrote describes a tool that behaves that way, or whether the flow
holds together. That gap is where most of this kit's recorded defects have lived. Review is
read-only, so it costs you nothing but the reading.

Then run the kit linter **against the personal root** —
`node <home>/upstream/tools/lint/aos-lint.mjs --root <home>/personal` (without
`--root` it lints the kit and reports green on a package it never opened) — the new
package must add zero errors — and show the user the full file tree plus a one-line summary of each new file.

**Then, the contribute question — judgment-gated, never reflexive.** Run the
generality judgment (capability-lifecycle's overlay reference, "Promote and retire":
stranger test, dependency test, coherence test, the maintenance-willingness question,
the ledger search):

- **Clearly generally useful** → ask, once: *"Want to contribute this?"* Yes →
  duplicate the package onto a branch in `<home>/upstream`, run the self-containment
  scrub again on the copy, and continue per the {{skill: contribute}} skill's
  contribute reference — the PR opens only on the user's explicit confirm.
- **Clearly niche** (their org's CRM, their home server) → no prompt; one soft line:
  *"kept in personal/ — say 'contribute it' anytime."*
- **Borderline** → suggest a `promotion-signal` issue instead ("would others want
  X?") — filed only on explicit yes.
