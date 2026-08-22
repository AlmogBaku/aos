# Codex cheat-sheet

## Contents

- Primitive mapping
- Materialization guide
- Introspection guide
- Secrets
- Removal
- Feature notes


Knowledge for the Codex CLI/desktop agent installing, introspecting, or removing aos
capabilities. The aos half is the `capability-lifecycle` entry skill's install contract;
this sheet is only the Codex half.

## Primitive mapping

| aos concept | Codex primitive | Where / how |
|---|---|---|
| front agent (`main`) | the current Codex session | shared; no front-agent file is created |
| skill | Agent Skills folder — a **symlink** to the pinned render in `<home>/personal` | `~/.codex/skills/<installed-name>/` |
| agent | session subagent | ephemeral; no persistent agent definition is materialized |
| context block | global `AGENTS.md` | `~/.codex/AGENTS.md`; append only inside aos marker pairs |
| tool on PATH | ordinary executable | `uv tool install` makes capability tools available normally |
| schedule | none | use the capability's declared degraded mode; do not create a system cron as an invisible substitute |
| secret | no Codex-local store assumed | see Secrets |
| plan mode | native plan mode when available | use it for read-only planning; otherwise prompt-enforce the gate |

Files Codex consumes for this integration are `~/.codex/skills/*/SKILL.md` and
`~/.codex/AGENTS.md`. Do not invent Codex-owned files or copy pinned renders.

## Materialization guide

1. Render each aos skill under
   `<home>/personal/capabilities/<capability>/skills/<installed-name>/`.
2. Symlink the whole directory into `~/.codex/skills/<installed-name>`; never copy it.
   Run the `aos-cap skills --check` name gate against `~/.codex/skills` first.
3. Append aos-owned context only inside its named marker pair in
   `~/.codex/AGENTS.md`. Preserve all non-aos instructions.
4. Do not materialize capability agents or schedules. Agent-only functionality and
   scheduled work follow their declared degraded mode.

## Introspection guide

- Skills: `rg --files ~/.codex/skills -g SKILL.md`; inspect links with
  `find ~/.codex/skills -maxdepth 1 -type l`.
- Context: `cat ~/.codex/AGENTS.md`.
- aos state: `aos-cap --home <home> list`, `show <id>`, and `verify`.

## Secrets

Never write secrets to `AGENTS.md`, a skill, a render, or `personal/`. Use an explicitly
configured external secret mechanism only when the user provides one; otherwise treat
secret-dependent functionality as unavailable and take the declared degraded mode.

## Removal

Walk the lockfile entry backwards: remove recorded skill symlinks, then aos marker blocks,
then rendered artifacts and the lockfile entry through the lifecycle capability. Preserve
`MOD.md`.

## Feature notes

Global skills and persistent instructions are supported. Codex session subagents are
ephemeral, and native persistent schedules and a local secret store are not assumed;
agent-, schedule-, or secret-dependent features may therefore degrade to manual operation.
