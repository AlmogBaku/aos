---
x-aos-origin: capability-lifecycle@0.1.0
name: capability-lifecycle
description: The aos capability lifecycle's front door. Use when the user asks to install, update, upgrade, remove, or customize an aos capability, mentions or shares a CAPABILITY.md or a capability directory, asks what capabilities are installed or what aos is, or asks about the manifest, the lockfile, or a harness cheat-sheet — and no narrower lifecycle skill matches.
---

# capability-lifecycle — the map

Capabilities are self-describing prompts; **you are the installer**. Judgment is yours;
bookkeeping is `aos-lock`'s (`aos-lock --help` — the lockfile is its file, never edit
the YAML). The diff gate is never optional. `MOD.md` is the user's ledger of
personalization: you re-apply it, you never overwrite it. The full rules:
`reference/contract.md`. The overlay doctrine (interviews, transform, capture):
`reference/overlay.md`.

| Ask | Skill |
|---|---|
| "install <capability>" · a capability offered for install | `capability-installer` |
| "update" / "upgrade" (kit-wide or one capability) | `capability-upgrader` |
| "remove/uninstall <capability>" | `capability-remover` |
| "change how <capability> behaves for me" | `capability-evolver` |
| "what's installed?" | `aos-lock list` |
| your harness's mapping | `harnesses/<harness-runtime>.md` (this capability); none → `reference/no-cheatsheet.md` |

Manifest quick facts: CAPABILITY.md frontmatter is strict-typed (`aos-lock manifest
<dir>` parses and validates it — its errors name the field and rule); predefined fields
only, `x-*` reserved for extensions; the prose below the frontmatter is the installer's
briefing, never runtime context.

## Experience

Every lifecycle interaction is **warm + expert: concept before mechanics,
explain-then-act**. Before doing anything visible, say what is about to happen and what
it buys the user — then proceed; the diff gate is the safety net, not repeated consent
prompts. Batch questions; if you can infer it, don't ask. Set expectations before slow
steps ("installing the tool takes a minute"). Show the gate as a payoff: each artifact →
what it does for you. Close with a specific, celebratory summary — what was installed,
where, which schedules, any degraded modes — never a vague "done." User-facing lines are
warm prose; your internal steps stay silent.
