---
harness: codex
status: verified
source: "real install 2026-08-22 (Codex CLI 0.149.0); official Codex CLI docs; github.com/openai/codex; 2026-10-20 research"
rules:
  - Codex has no native scheduler; use the capability's declared degraded mode rather than creating an invisible system cron
files: [~/.agents/skills/*/SKILL.md, ~/.codex/AGENTS.md]
mapping:
  agent:
    support: none
    instead: ephemeral session subagents only — no persistent agent definition is materialized; agent-dependent features take the declared degraded mode
  main:
    primitive: the current Codex session — shared; no front-agent file is created
    where: ~/
  skill:
    primitive: Agent Skills folder — a symlink to the pinned render in <aos_home>/personal
    where: ~/.agents/skills/<installed-name>
    unverified: [where]
    note: "research 2026-10-20: vercel-labs/skills PR #2067 and intellectronica/ruler issue #585 report global skills moved from ~/.codex/skills (legacy) to ~/.agents/skills; confirm against the running build and update this row either way"
  cron:
    support: none
    instead: declared degraded mode; for unattended runs use the ChatGPT web or desktop app automations
    note: "research 2026-10-20: the Codex CLI has no scheduler; the desktop app and ChatGPT have scheduled tasks/automations — 'Codex CLI doesn't provide the Scheduled management interface. Use ChatGPT web or the desktop app' (learn.chatgpt.com/docs/automations?surface=app)"
  context_block:
    primitive: global AGENTS.md — append only inside aos marker pairs
    where: ~/.codex/AGENTS.md
  secret:
    support: none
    instead: use an explicitly configured external mechanism the user provides; absent ⇒ take the capability's declared degraded mode
  config:
    primitive: ~/.codex/config.toml (TOML)
    where: ~/.codex/config.toml
    set: "edit ~/.codex/config.toml directly"
  hook:
    primitive: hook definitions in ~/.codex/hooks.json or [hooks] in ~/.codex/config.toml
    consent: approve each by exact command via /hooks in the TUI; never --dangerously-bypass-hook-trust
    check: "/hooks (shows Trusted); codex doctor does not check hook trust"
    revoke: remove the entry from hooks.json or config.toml
  session:
    support: unknown
    note: "research 2026-10-20: `codex exec` sessions have no title and are hidden from the default resume picker; continue via `codex exec resume <session_id> <prompt>`; titled sessions need the app-server protocol (github.com/openai/codex codex-rs/exec, codex-rs/tui); an in-session /fork exists besides `codex fork --last` (cwd-filtered)"
  plan_mode:
    primitive: native plan mode (when available); prompt-enforce the gate if absent
  calendar.read:
    support: unknown
  calendar.write:
    support: unknown
  email:
    support: unknown
  messaging.inbound:
    support: unknown
  messaging.outbound:
    support: unknown
  voice.stt:
    support: unknown
  voice.tts:
    support: unknown
---
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

**Rule zero** (`rules`): Codex has no native scheduler (`mapping.cron`). Do not create a
system cron as an invisible substitute — it is outside the harness and invisible to `verify`
and `remove`. Use the capability's declared degraded mode (`manual` = invocable skill,
`skip` = skip). For unattended runs, the ChatGPT web or desktop app automations are the
correct path.


## Primitive mapping

The frontmatter's `mapping` is the glossary. What follows is the judgment the rows cannot
carry.

- **Agent** (`mapping.agent`): Codex session subagents are ephemeral — there is no
  persistent agent definition. Agent-dependent features take the declared degraded mode.
  `workspace: shared` ⇒ fold into the main session.
- **Skill** (`mapping.skill`): global skills live at `mapping.skill.where`, which carries
  `unverified: [where]` — the location moved from `~/.codex/skills` (legacy) to
  `~/.agents/skills` per two independent issue reports; confirm against the running build
  and update this row either way. Codex follows symlinked skill dirs. Run the
  `aos-cap skills --check` name gate against the confirmed skills root before linking.
- **Session branch** (`mapping.session`): `codex fork --last` (in a second terminal) copies
  the most recent session; an in-session `/fork` also exists. `codex resume <session>`
  reopens the original. Neither form is template-shaped yet — details in
  `mapping.session.note`.
- **Files** (`files`): `AGENTS.md` and skills are the only harness-consumed files. Do not
  copy pinned renders; symlink only.

`model_class` mapping: only set the model when the harness's default doesn't already fit
the class; never hardcode provider names.


## Materialization guide

1. Render each aos skill under
   `<aos_home>/personal/capabilities/<capability>/skills/<installed-name>/`.
2. Symlink the whole directory into the skills root at `mapping.skill.where`. Confirm the
   current root on the running build — the legacy `~/.codex/skills` path may still apply.
   Run the `aos-cap skills --check` name gate first. Never copy.
3. Append aos-owned context only inside its named marker pair in `~/.codex/AGENTS.md`.
   Preserve all non-aos instructions.
4. Do not materialize capability agents or cron jobs (`mapping.agent`, `mapping.cron`).
   Agent-only and scheduled features follow their declared degraded mode.
5. Hooks: register in `~/.codex/hooks.json` or `[hooks]` in `~/.codex/config.toml` per
   `mapping.hook`. Project `.codex/` overlays load only when `projects.<path>.trust_level`
   is set; append only — trust keys are positional, so inserting ahead of existing hooks
   drops their trust. New or changed non-managed hooks are skipped until trusted: the TUI
   prompts "Hooks need review"; `codex exec` skips silently. Approve each by its exact
   command through `/hooks` in the TUI — never `--dangerously-bypass-hook-trust`, "Trust
   all and continue", or a managed layer (`/etc/codex`, `requirements.toml`). Trust keys on
   the definition, not the script. Don't claim the `notify` slot (single ungated user slot).
   Verify: `mapping.hook.check`.


## Introspection guide

- Skills: `rg --files <skills-root> -g SKILL.md`; inspect links with
  `find <skills-root> -maxdepth 1 -type l`. Confirm `<skills-root>` on the running build
  per `mapping.skill.where`.
- Context: `cat ~/.codex/AGENTS.md`.
- aos state: `aos-cap --home <aos_home> list`, `show <id>`, and `verify`.


## Secrets

Never write secrets to `AGENTS.md`, a skill, a render, or `personal/`
(`mapping.secret`). Use an explicitly configured external mechanism only when the user
provides one; otherwise treat secret-dependent functionality as unavailable and take the
declared degraded mode.


## Removal

Walk the lockfile entry backwards: remove recorded skill symlinks, then aos marker blocks,
then rendered artifacts and the lockfile entry through the lifecycle capability. Preserve
`MOD.md`.


## Feature notes

Global skills and persistent instructions are supported. Codex session subagents are
ephemeral (`mapping.agent`), native persistent cron jobs do not exist (`mapping.cron`),
and a local secret store is not assumed (`mapping.secret`); agent-, cron-, or
secret-dependent features degrade to manual operation.

The `depends.host` rows `mapping.messaging.inbound`, `mapping.messaging.outbound`,
`mapping.voice.stt`, `mapping.voice.tts`, `mapping.calendar.read`, `mapping.calendar.write`,
and `mapping.email` were not established in the research (`support: unknown`); verify
against the running build before relying on them.
