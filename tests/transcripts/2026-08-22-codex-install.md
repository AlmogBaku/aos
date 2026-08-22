# Codex install e2e — 2026-08-22

## Environment

- Harness: Codex CLI 0.149.0.
- Household: a local `~/aos/` installation with `upstream/`, private `personal/`, and
  machine-local `.aos/` state.
- Codex primitives exercised: global skills at `~/.codex/skills/` and global context at
  `~/.codex/AGENTS.md`.

## Install result

Bootstrap installed `capability-lifecycle` and then `kb`. The harness contains 17 aos-owned
skill symlinks: ten lifecycle skills and seven kb skills. The lifecycle capability recorded
two marker-owned blocks in `~/.codex/AGENTS.md` (`mode-boundary` and `concepts`); no files
outside those markers were owned by aos.

`aos-cap --home ~/aos verify` returned `clean: 2 entries verified`. The name gate, rendered
skill provenance, symlink targets, and lockfile artifacts were checked after installation.

## Harness limits observed

- Codex subagents are session-scoped; no persistent agent definition was materialized.
- No Codex-native local scheduler or secret store was used. No schedules were created.
- The system `skill-creator` was already owned by Codex, so it was recorded as a referenced
  artifact rather than copied or vendored.

## Isolation check

`CODEX_HOME` was exercised with a disposable home for this contribution. Codex created its
own system skills and state under that isolated directory, confirming that AOS can target a
separate Codex installation without touching the active user home. The disposable agent run
was intentionally not used as the install witness because the CLI's `--ephemeral` mode does
not retain a resumable rollout; the completed household install above is the e2e witness.
