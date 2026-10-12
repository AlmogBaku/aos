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
| session branch | CLI only — `codex fork --last` (in a second terminal) copies the most recent session into a new one; `codex resume <session>` reopens the original | capability-build hands the user both commands. From the CLI's help; unverified in a live session |

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
5. Hooks: register in `~/.codex/hooks.json` or `[hooks]` in `~/.codex/config.toml`
   (project `.codex/` overlays load only when `projects.<path>.trust_level` is set; append
   only — trust keys are positional, so inserting ahead of existing hooks drops their
   trust). New or changed non-managed hooks are skipped until trusted: the TUI prompts
   "Hooks need review"; `codex exec` skips silently (source-inferred). Approve each
   declared hook by its exact command through `/hooks` in the TUI — never
   `--dangerously-bypass-hook-trust`, "Trust all and continue", or a managed layer (`/etc/codex`,
   `requirements.toml`); trust keys on the definition, not the script. Don't claim `notify`
   (single ungated user slot). Verify: `/hooks` shows `Trusted`; `codex doctor` does not
   check hook trust.

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
