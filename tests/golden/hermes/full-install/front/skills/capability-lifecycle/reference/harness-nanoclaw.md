---
harness: nanoclaw
status: research-drafted
source: "nanocoai/nanoclaw (calendar versioning; current 2026.10.0); <DATE> research"
rules:
  - never hand-edit generated files or the state DB — v2 CLAUDE.md and container.json are regenerated at every container spawn; every mutation goes through ncl (v2) or the main agent's own tools (v1)
files: [groups/<f>/instructions.prepend.md, groups/<f>/memory/, groups/<f>/CLAUDE.md,
        .claude/skills/*/SKILL.md, .env, .mcp.json]
mapping:
  agent:
    primitive: agent group — a per-group Docker container
    where: {v2: "DB row + groups/<f>/ (materializes on first message)", v1: "registered_groups DB row keyed by chat JID, folder {channel}_{group-name}"}
    create: "v2: ncl groups create --name <n> --folder <f>; v1: register via the main agent"
  main:
    primitive: "v2: the setup wizard's first group (no privileged tier); v1: the is_main=1 group"
    where: {v2: "first group's groups/<folder>/", v1: "groups/<is_main_folder>/"}
    note: "default assistant name Andy (ASSISTANT_NAME)"
  skill:
    primitive: Agent Skills folder in .claude/skills/<installed-name>/ — a symlink to the pinned render in <aos_home>/personal
    where: .claude/skills/<installed-name>/
    note: "auto-registered as /<installed-name>; pass .claude/skills to the name gate --harness-skills. Container mount requirement: links resolve inside containers only if <aos_home>/personal is mounted read-only into the group (ncl groups config add-mount --ro <aos_home>/personal) — do this once per group at first aos install, before any skill link; without it, stop and say so (never fall back to copying). v2 per-group scoping via ncl groups config skills field; v1 mount path unverified"
  cron:
    primitive: DB-driven task — host sweep every 60 s (NOT OS cron); precision ±60 s + container cold start
    where: v2 sessions DB; v1 scheduled_tasks table
    create: "v2: ncl tasks create --prompt '<prompt_ref>' --name 'aos:<capability>:<cron-id>' --recurrence '<expr>' --group <agent-id>"
    exec: "system crontab line with # aos:<cap>:<id> comment (no verified script-only task form)"
    note: "v1: ask the main agent in natural language, then read the scheduled_tasks row back and verify name + prompt. One-shot: --process-after <ts>. Cron parsed by cron-parser in instance TZ"
  context_block:
    primitive: "v2: groups/<f>/instructions.prepend.md (standing instructions) + groups/<f>/memory/ — composed into generated CLAUDE.md at spawn; v1: groups/<f>/CLAUDE.md directly; global memory groups/global/CLAUDE.md (main writes, all read)"
    where: {v2: "groups/<f>/instructions.prepend.md", v1: "groups/<f>/CLAUDE.md"}
    note: "no SOUL.md, no AGENTS.md in either version — do not invent files"
  secret:
    primitive: .env line at checkout root; v2 optionally the OneCLI Agent Vault
    where: .env at checkout root
    store: nanoclaw-env
    note: "OneCLI-managed values are gateway-injected and never resolvable as aos references — capability secret references stay {store: nanoclaw-env} either way"
  config:
    primitive: v2 ncl groups config fields; v1 container_config JSON column
    where: {v2: "ncl groups config update --id <id> …", v1: "container_config JSON column"}
    set: "v2: ncl groups config update --id <id> --<field> <value>; ncl groups config add-mcp-server | add-package | add-mount"
  hook:
    primitive: command hook written into data/v2-sessions/<agent-group-id>/.claude-shared/settings.json (the container's ~/.claude)
    consent: "NanoClaw's Claude provider runs bypassPermissions — no consent gate; the diff gate is the only review"
    check: "read data/v2-sessions/<agent-group-id>/.claude-shared/settings.json back to confirm"
    revoke: "remove the entry from the settings.json in the session dir"
    note: "silent wall: a path outside allowedRoots in ~/.config/nanoclaw/mount-allowlist.json is dropped at spawn; add only the specific root needed (never ~ or /), ncl groups restart, grep logs/nanoclaw.log for no REJECTED. Script paths must resolve inside the container"
  session:
    support: none
    instead: "no titled sessions — the nearest is `ncl messaging-groups send`, which injects into the user's chat and wakes the agent"
  plan_mode:
    support: none
    instead: prompt-enforced — declare "planning — no writes until approval" and hold it; v2 approval-gated config mutations are adjacent machinery, not a plan mode
  calendar.read:
    support: via
    via: v2 installable /add-gcal-tool (Google Calendar MCP tool); v1 has no calendar support
  calendar.write:
    support: via
    via: v2 installable /add-gcal-tool (Google Calendar MCP tool); v1 has no calendar support
  email:
    support: via
    via: v2 /add-gmail-tool (read/search/send/label/draft) + /add-resend outbound; v1 add-gmail skill
  messaging.inbound:
    primitive: adapter → router → container; v2 adds attachments, mentions, question cards
  messaging.outbound:
    primitive: "v2 MCP tools send_message, send_file, edit_message, add_reaction, send_card, ask_user_question — send-only; v1 verified only send_message"
  voice.stt:
    support: none
    note: "v2 has no voice transcription; v1 installable /add-voice-transcription (absent from the v2 catalog)"
  voice.tts:
    support: none
---
# NanoClaw cheat-sheet

## Contents

- Primitive mapping
- Materialization guide
- Introspection guide
- Secrets
- Removal
- Feature notes


Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
NanoClaw. The aos half is the `capability-lifecycle` entry skill's install contract; this
sheet is only the NanoClaw half. One sheet covers **v2** (current) and **v1** (frozen;
migration is `/migrate-from-v1`): each concept is stated once, and where the execution
surface differs it splits inline as "v2: `ncl …` · v1: ask the main agent / edit editable
files".

> [!WARNING]
> Research-drafted: no aos e2e install has run on NanoClaw yet (support-matrix honesty,
> ARCHITECTURE §5.3). Verify each mapping against the live install as you use it, and
> fix-and-PR anything wrong.

**Rule zero** (`rules`): never hand-edit generated files or the state DB. v2's
`groups/<folder>/CLAUDE.md` (it begins `<!-- Composed at spawn - do not edit. … -->`) and
`groups/<folder>/container.json` are regenerated at every container spawn — hand-writes are
silently overwritten. The DBs (v2 `data/v2.db`, v1 `store/messages.db`) hold live
router/scheduler state. Every mutation goes through `ncl` (v2) or the main agent's own
tools (v1). The editable v2 context file is `groups/<folder>/instructions.prepend.md`.

**Version detection** (read-only signals): v2 has `data/v2.db` (+ `data/v2-sessions/`),
`nanoclaw.sh`, an `ncl` CLI on PATH, `src/host-sweep.ts`, and generated per-group
`CLAUDE.md` starting with the do-not-edit comment. v1 has `store/messages.db`,
`setup.sh` (no `nanoclaw.sh`), no `ncl`, `src/task-scheduler.ts`, and hand-edited
`groups/<folder>/CLAUDE.md` plus `groups/global/CLAUDE.md`. The repo has moved to
`nanocoai/nanoclaw` and switched to calendar versioning (current `2026.10.0`), so
`package.json`'s major version is no longer a reliable signal — use the filesystem signals
above.


## Primitive mapping

The frontmatter's `mapping` is the glossary: each aos concept and each `depends.host` word →
the NanoClaw primitive, where it lives, and the one command a template can hold. What
follows is the judgment the rows cannot carry.

- **Agent** (`mapping.agent`): v2 wires a group to a chat with `ncl messaging-groups create`
  then `ncl wirings create --engage-mode pattern --engage-pattern '^[Ss]cout\b'`; smoke-test
  with `pnpm run chat <folder> "hi"` (cold start 30–60 s). v1: ask the main agent to
  register the chat.
- **Skill** (`mapping.skill`): auto-registered as `/<installed-name>`, so the slash-command
  namespace is the skill namespace — pass `.claude/skills` to the name gate's
  `--harness-skills`. The container mount requirement in `mapping.skill.note` must be
  satisfied before the first skill link; without it stop and say so. No build; agent
  containers see skills mounted read-only at `/app/skills` (v2 — v1 mount path unverified).
- **Cron** (`mapping.cron`): DB-sweep task, ±60 s + container cold start — NOT OS cron;
  v1 also supports interval/once kinds.
- **Session** (`mapping.session`): there are no titled sessions. The nearest equivalent is
  `ncl messaging-groups send`, which injects into the user's chat and wakes the agent
  (`instead:` in the mapping row).
- **Files** (`files`): anything else you write is inert. No `SOUL.md`, no `AGENTS.md` in
  either version — do not invent files.

`model_class` mapping: only set `ncl groups config update --id <id> --model <model>
--effort <level>` (v1: the `container_config` JSON column) when the group's default doesn't
already fit the class; never hardcode provider names.


## Materialization guide

1. **Agents → agent groups.** v2: per `mapping.agent.create`; wire to a chat and smoke-test.
   v1: ask the main agent to register the chat as a group. `purpose` + persona content →
   v2 `instructions.prepend.md` (then `ncl groups restart --id <id>`) · v1
   `groups/<f>/CLAUDE.md`.
2. **Skills**: `aos-cap skills <cap-dir>` gives the installed name; the render lives once
   at `<aos_home>/personal/capabilities/<capability>/skills/<installed-name>/` (contract);
   symlink it as `.claude/skills/<installed-name>` and record the link
   (`aos-cap record … --link`). Verify the group's `<aos_home>/personal` ro mount first
   per `mapping.skill.note`. Never copy. Scope per `used_by` via the v2 group config
   `skills` field; v2 skills that leave artifacts ship a sibling `REMOVE.md`. Channel
   plumbing comes from registry slash-skills (`/add-telegram`, …) — additive, idempotent,
   reversible; only `cli` is built in.
3. **Cron jobs.** Agent-type entries (`agent` + `prompt_ref`): v2 per `mapping.cron.create`.
   v1 per `mapping.cron.note`. One-shot: `--process-after <ts>`. Exec-type entries
   (`exec:`): use `mapping.cron.exec` (system crontab fallback — no verified script-only
   task form). Single-owner check = `ncl tasks list --all` (v1: read `scheduled_tasks`).
4. **Context blocks** → marker-delimited appends per `mapping.context_block.where` (v2:
   restart the group after editing `instructions.prepend.md`).
5. **Config**: v2 per `mapping.config.set`. Mutations are approval-gated — expect a pending
   approval, not instant effect. Record every field set in the lockfile. v1: `container_config`
   JSON column (example `config-examples/mount-allowlist.json`).
6. **Command hooks.** No consent gate — NanoClaw's Claude provider runs
   `bypassPermissions`. Write a command hook per `mapping.hook.consent` guidance;
   fires inside the container, scheduled runs too. Mount-allowlist wall:
   `mapping.hook.note`. Verify per `mapping.hook.check`.


## Introspection guide

- v2 (`--json` for machine output; `--limit N`, default 200): `ncl groups list|get`,
  `ncl groups config get`, `ncl messaging-groups list`, `ncl wirings list|get`,
  `ncl destinations list`, `ncl members|roles|users list`,
  `ncl tasks list [--status pending|paused] [--group] [--all]`, `ncl tasks get --id <series>`,
  `ncl sessions list [--status active]`, `ncl approvals|policies|dropped-messages list`,
  `ncl help`.
- Containers: `docker ps --filter name=nanoclaw-v2-<folder>`. Logs: host `LOG_LEVEL`, the
  `/debug` skill; optional `/add-clidash` read-only dashboard.
- DB, read freely / write never: `data/v2.db` (agent_groups, container_configs,
  messaging_groups, sessions, pending_approvals, …).
- v1: no `ncl` — read `store/messages.db` (registered_groups, scheduled_tasks, messages,
  chats, sessions) or ask the main agent; list `.claude/skills/`; read
  `groups/<f>/CLAUDE.md`, `groups/global/CLAUDE.md`, `conversations/`; pino logs; macOS
  service under `launchd/`.


## Secrets

- Values → `.env` at checkout root (host-read; parsed by `src/env.ts`). Never echo values.
- Reference store (`mapping.secret.store`): resolve = read that variable from the checkout
  `.env`. v1 has `.env` only.
- v2 optional OneCLI Agent Vault (`/init-onecli`): an HTTPS-proxy gateway injects real
  Authorization headers in-flight, so raw keys never enter agent containers; stub files
  literally contain `onecli-managed` — never "fix" them. Opt out with
  `/use-native-credential-proxy`; env `ONECLI_URL`/`ONECLI_API_KEY`; egress lockdown via
  `NANOCLAW_EGRESS_LOCKDOWN`/`NANOCLAW_EGRESS_NETWORK`. OneCLI-managed values are
  gateway-injected and never resolvable — capability references stay `{store: nanoclaw-env}`
  either way.
- There is no MCP get-secret tool — never write a prompt that assumes an agent can fetch a
  secret by name.


## Removal

Drive everything from the lockfile entry, in order:

1. Tasks: v2 `ncl tasks cancel --id <series>` (keeps history) or `ncl tasks delete
   --id <series>` per `cron_owned` id (`pause|resume` for temporary stops); v1: ask the
   main agent to remove the task, then verify the `scheduled_tasks` row is gone.
2. Skills: run the sibling `REMOVE.md` first (v2), then delete the
   `.claude/skills/<installed-name>` symlink; the render dirs in `<aos_home>/personal` are
   deleted via a commit (contract). The `<aos_home>/personal` mount stays if any other aos
   capability is installed in the group.
3. Context blocks: strip the `<!-- aos:<capability>… -->` marker blocks from v2
   `instructions.prepend.md` (then `ncl groups restart`) / v1 `groups/<f>/CLAUDE.md`.
4. Config: v2 `ncl groups config remove-mcp-server|remove-package|remove-mount` per
   recorded field.
5. `.env` lines added at install: remove after asking the user.
6. Groups created by this capability and used by nothing else: v2 `ncl groups delete
   --id <id>` (cascades wirings, config, sessions); orphaned plumbing via
   `ncl wirings delete` and `ncl messaging-groups delete`. v1: the main agent's
   remove-group (deletes the DB row + `groups/<folder>/`).
7. Remove the lockfile entry; verify per the contract (re-run Introspection).

Whole-harness uninstall (not per-capability): v2 `bash nanoclaw.sh --uninstall`
(`--dry-run`, `--yes`); leftover containers
`docker ps -aq --filter label=nanoclaw-install=<slug> | xargs -r docker rm -f`. v1 has no
uninstall script — manual cleanup plus stopping the `launchd/` service.


## Feature notes

The `depends.host` rows of `mapping` answer which features exist here.

`mapping.calendar.read`, `mapping.calendar.write`, and `mapping.email` are present only
when the respective installable slash-skill is enabled (v2); absent ⇒ apply the cron job's
`degraded:` mode. `mapping.voice.stt` has no v2 implementation (v1 only via
`/add-voice-transcription`); `mapping.voice.tts` has none in either version.

Degraded-mode wiring: `manual` ⇒ the invocable skill lands in `.claude/skills/` scoped
(v2 `skills` field) to the group that would have owned the job; `inline` ⇒ no verified
task-edit verb exists — cancel the owning task and recreate it under the same `aos:` name
with the appended prompt.

Channels beyond built-in `cli` are all installable slash-skills: WhatsApp (Baileys + Cloud
API), Telegram, Discord, Slack, Signal, iMessage, Teams, Google Chat, GitHub, Linear,
Matrix, Webex, WeChat, Delta Chat, Emacs, Resend. The v1 set was smaller: WhatsApp
(flagship), Telegram, Discord, Slack, Gmail — WhatsApp auth is `npm run auth` (QR).
