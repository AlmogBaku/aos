# Capability: session

**Tags:** infra · **Build order:** 4 · **Seam it proves:** a capability tool that reaches the harness through the recorded absolute CLI, driven by the cheat-sheet `mapping.session` row, with no harness name in its code

## Scope

Opens titled sessions and delivers notices into the session that asked. Two commands:

- **`aos-session open --profile <p> --title <t> [--prompt-file <f>] [--workdir <d>]`** — opens one new titled session; the title is suffixed with the local time (`HH:MM`). Reports `Opened "<title> HH:MM" (session <id>) in profile <p>.`
- **`aos-session notify --profile <p> --session <id> --prompt-file <f> --title <t>`** — adds a turn to the session that asked for the work. If the harness reports that session gone (`mapping.session.missing` — the exact text from the L0 probe), opens a new notification session instead. Any other failure exits non-zero (no stray session, no silent swallow). No fallback of its own — each use case decides what to do on a non-zero exit.

The tool reads `<aos_home>/.aos/harness.yml` and the installed cheat-sheet's `mapping.session` row; it runs the recorded absolute harness CLI (`cli` field). No harness name appears in its code.

**There is no `open-session` capability.** `open-session` was replaced by this capability (ALM-51). The ghost of `open-session` is importable as a reference source; it must not be reinstalled.

## What exists today (extraction sources)

- `open-session` in the household: the session-opening logic that `open-session` performed via Hermes internals, abstracted to a CLI shim that reads `harness.yml`.
- The ghostwriter capability: its session-open usage at the start of an interview (one `aos-session open` call per interview).
- The Artificial Thoughts close-hook runner: its notify usage after archiving a guest memo.

## Depends

`capabilities: [capability-lifecycle]` — requires `aos-cap harness set <runtime>` to have been run (writes `harness.yml`). No `depends.host` word: `session` is a concept row in the cheat-sheet mapping, not a separate host feature; its `support` value drives behavior.

## Onboarding sketch

None. The harness record (`harness.yml`) is machine-local state written by the capability-lifecycle onboarding (`aos-cap harness set`); no interview questions belong here.

## v0.1 acceptance

`open --title "Interview"` runs the recorded harness CLI with the title `"Interview HH:MM"` and reports the opened session id. `notify` with a live session id adds a turn and exits 0. `notify` with a session id the harness reports as gone (matching `mapping.session.missing`) opens a new session and exits 0. `notify` with any other failure exits non-zero with a one-line log — no new session is opened. All runs succeed off-PATH by using the recorded `cli` absolute path. `--version` matches the packaged version string.
