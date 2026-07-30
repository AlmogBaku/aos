---
name: capability-lifecycle
description: "The aos capability lifecycle's front door. Use when the user asks to install, update, upgrade, remove, or customize an aos capability, mentions or shares a CAPABILITY.md or a capability directory, asks what capabilities are installed or what aos is, or asks about the manifest, the lockfile, or a harness cheat-sheet. Routes to the narrower skill that owns the job — capability-install, capability-upgrade, capability-remove, capability-onboard, capability-evolve, capability-import, capability-build, capability-contribute, capability-review — and carries the household layout, the install contract and the naming rules they all share. Do NOT use when one of those already matches the ask; this is the map, not the work."
---

# capability-lifecycle — the map

Capabilities are self-describing prompts; **you are the installer**. Judgment is yours;
bookkeeping is `aos-lock`'s (`aos-lock --help` — the lockfile is its file, never edit
the YAML). Everything lives in the household `<home>` (default `~/aos`): `upstream/`
the pristine kit clone, `personal/` the user's private repo (their MOD files, the
pinned renders harnesses symlink to, their private capabilities), `.aos/` machine
state. The diff gate is never optional. `MOD.md` states the user's
personalization — what they changed from the shipped defaults, current state, edited in
place: you re-apply it, you never overwrite it — and you never write anything
to upstream (PR, issue, +1, push, fork, remote branch) without the user's explicit
approval. The full rules:
`reference/contract.md`. The overlay doctrine (interviews, transform, capture,
promote/retire, persist): `reference/overlay.md`. Naming, installed skill names, and the
uniqueness gate: `reference/naming.md` — read it before authoring or installing anything
that ships a skill.

| Ask | Skill |
|---|---|
| "install <capability>" · a capability offered for install | `capability-install` |
| "update" / "upgrade" (kit-wide or one capability) | `capability-upgrade` |
| "remove/uninstall <capability>" | `capability-remove` |
| "run/redo my interview" · bootstrap a new user | `capability-onboard` |
| "wrap what I already built into a capability" | `capability-import` |
| something recurring/systemic to build | `capability-build` |
| "fix/change <capability> for everyone" · contribute upstream | `capability-contribute` |
| "change how <capability> behaves for me" | `capability-evolve` |
| "promote my tweak" / "this should be for everyone" | `capability-evolve` classifies, then hands to `capability-contribute` |
| "review/audit <capability>" · before contributing · "something looks wrong here" | `capability-review` — read-only, architecture first |
| "what's installed?" | `aos-lock list` |
| your harness's mapping | `reference/harness-<harness-runtime>.md` — an aid, not a gate: loaded per operation, never standing context; none → `reference/no-cheatsheet.md` |

Manifest quick facts: CAPABILITY.md frontmatter is strict-typed (`aos-lock manifest <dir>` parses and validates it — its
errors name the field and rule); the fields are `id · version · tags · summary · depends · schedules · skills · skill_prefix · kb`, `x-*`
reserved for extensions; the prose below the frontmatter is the installer's
briefing, never runtime context. A skill's id is capability-local — the name it installs
under is `aos-lock skills <dir>`'s answer, and it is single-owner across the whole harness
(`reference/naming.md`).

## Experience

Every lifecycle interaction is **warm + expert: concept before mechanics,
explain-then-act**. Before doing anything visible, say what is about to happen and what
it buys the user — then proceed; the diff gate is the safety net, not repeated consent
prompts. Batch questions; if you can infer it, don't ask. Set expectations before slow
steps ("installing the tool takes a minute"). Show the gate as a payoff: each artifact →
what it does for you. Close with a specific, celebratory summary — what was installed,
where, which schedules, any degraded modes — never a vague "done." User-facing lines are
warm prose; your internal steps stay silent.
