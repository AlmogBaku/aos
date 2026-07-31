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
sheet is only the NanoClaw half. One sheet covers **v2** (current) and **v1** (frozen at v1.2.0;
migration is `/migrate-from-v1`): each concept is stated once, and where the execution
surface differs it splits inline as "v2: `ncl …` · v1: ask the main agent / edit editable files".

> [!WARNING]
> Research-drafted: no aos e2e install has run on NanoClaw yet (support-matrix honesty,
> ARCHITECTURE §5.3). Verify each mapping against the live install as you use it, and
> fix-and-PR anything wrong.

**Rule zero: never hand-edit generated files or the state DB.** v2's `groups/<folder>/CLAUDE.md`
(it begins `<!-- Composed at spawn - do not edit. … -->`) and `groups/<folder>/container.json`
are regenerated at every container spawn — hand-writes are silently overwritten. The DBs
(v2 `data/v2.db`, v1 `store/messages.db`) hold live router/scheduler state. Every mutation
goes through `ncl` (v2) or the main agent's own tools (v1). The editable v2 context file is
`groups/<folder>/instructions.prepend.md`.

**Version detection** (read-only signals): v2 has `data/v2.db` (+ `data/v2-sessions/`),
`nanoclaw.sh`, an `ncl` CLI on PATH, `src/host-sweep.ts`, and generated per-group `CLAUDE.md`
starting with the do-not-edit comment. v1 has `store/messages.db`, `setup.sh` (no
`nanoclaw.sh`), no `ncl`, `src/task-scheduler.ts`, and hand-edited `groups/<folder>/CLAUDE.md`
plus `groups/global/CLAUDE.md`. Either way, `package.json`'s major version (1.x vs 2.x)
settles it.


## Primitive mapping

| aos concept | NanoClaw primitive | Where / how |
|---|---|---|
| agent | **agent group** — a per-group Docker container | v2: `ncl groups create --name <n> --folder <f>` (DB row + `container_configs`; `groups/<f>/` materializes on first message). v1: `registered_groups` DB row keyed by chat JID, folder `{channel}_{group-name}` — register via the main agent |
| front agent (`main`) | v2: no privileged tier ("privilege lives on users") — treat the setup wizard's first group as `main`. v1: the `is_main=1` group (no trigger word, sole writer of global memory, can register groups and schedule for any group) | default assistant name `Andy` (`ASSISTANT_NAME`) |
| skill | Agent Skills folder in the checkout's `.claude/skills/<installed-name>/` — a **symlink** to the pinned render in `<home>/personal` | auto-registered as `/<installed-name>`, so the slash-command namespace is the skill namespace — pass `.claude/skills` to the name gate's `--harness-skills`. No build; agent containers see skills mounted read-only at `/app/skills` (v2 — v1 mount path unverified). **Container mount requirement**: links resolve inside containers only if `<home>/personal` is mounted read-only into the group (`ncl groups config add-mount --ro <home>/personal`) — do this once per group at first aos install, before any skill link; without it, stop and say so (never fall back to copying). `used_by` scoping: v2 per-group `skills` field in `ncl groups config` (default `"all"`) |
| schedule | DB-driven **task**, host sweep every 60 s — NOT OS cron | v2: `ncl tasks create` → per-session `messages_in` rows (kind `task`, `recurrence` cron string, `series_id`). v1: `scheduled_tasks` table (cron\|interval\|once) via the main agent. Cron parsed by cron-parser in instance `TZ`; precision ±60 s + container cold start |
| context block | v2: `groups/<f>/instructions.prepend.md` (standing instructions) + `groups/<f>/memory/` — both composed into the generated `CLAUDE.md` at spawn. v1: `groups/<f>/CLAUDE.md` directly; global memory `groups/global/CLAUDE.md` (main writes, all read) | no `SOUL.md`, no `AGENTS.md` in either version — do not invent files |
| secret | `.env` line at checkout root; v2 optionally the OneCLI Agent Vault | see Secrets |
| plan mode | none native — prompt-enforced | declare "planning — no writes until approval" and hold it (v2's approval-gated config mutations are adjacent machinery, not a plan mode) |

Files NanoClaw consumes — anything else you write is inert:
`groups/<f>/instructions.prepend.md` (v2), `groups/<f>/memory/**` (v2),
`groups/<f>/CLAUDE.md` (v1 editable; v2 generated, read-only),
`.claude/skills/<name>/SKILL.md` (+ sibling `REMOVE.md`, v2), `.env`, `.mcp.json`, and the
state DB.

`model_class` mapping: only set `ncl groups config update --id <id> --model <model>
--effort <level>` (v1: the `container_config` JSON column) when the group's default doesn't
already fit the class; never hardcode provider names.

## Materialization guide

1. **Agents → agent groups.** v2: `ncl groups create --name "Scout" --folder scout`; wire to
   a chat with `ncl messaging-groups create --channel-type <t> --platform-id <id> --name <n>
   --unknown-sender-policy <p>` then `ncl wirings create --messaging-group-id <mg>
   --agent-group-id <ag> --engage-mode pattern --engage-pattern '^[Ss]cout\b'`; smoke-test
   `pnpm run chat scout "hi"` (cold start 30–60 s). v1: ask the main agent to register the
   chat as a group. `purpose` + persona content → v2 `instructions.prepend.md` (then
   `ncl groups restart --id <id>`) · v1 `groups/<f>/CLAUDE.md`.
2. **Skills**: `aos-lock skills <cap-dir>` gives the installed name; the render lives once
   at `<home>/personal/capabilities/<capability>/skills/<installed-name>/` (contract);
   symlink it as `.claude/skills/<installed-name>` and record the link
   (`aos-lock record … --link`). Verify the group's `<home>/personal` ro mount first
   (Primitive mapping). Never copy. Scope per `used_by` via the v2 group config `skills`
   field; v2 skills that leave artifacts ship a sibling `REMOVE.md` (no v1 `REMOVE.md`
   convention found — unverified). Channel plumbing comes from registry slash-skills (`/add-telegram`, …) —
   additive, idempotent, reversible; only `cli` is built in.
3. **Schedules.** Agent-type entries (`agent` + `prompt_ref`):

   ```
   ncl tasks create --prompt "<personalized prompt_ref content>" \
     --name 'aos:<capability>:<schedule-id>' --recurrence '<cron>' --group <agent-id>
   ```

   One-shot: `--process-after <ts>`. v1: ask the main agent in natural language, then read
   the `scheduled_tasks` row back and verify name + prompt. **Exec-type entries (`exec:`)**
   have no verified script-only task form — `--script <bash>` exists only as a gate on a
   prompt task; if a pure script job isn't achievable, fall back to a system crontab line
   with the same command and a `# aos:<cap>:<id>` comment, and record whichever was used in
   the lockfile. Single-owner check = `ncl tasks list --all` (v1: read `scheduled_tasks`).
4. **Context blocks** → marker-delimited appends per the mapping row (v2 restart the group
   after editing `instructions.prepend.md`).
5. **Config**: v2 `ncl groups config update --id <id> …` plus
   `add-mcp-server | add-package (--apt|--npm) | add-mount [--ro]`. Mutations are
   approval-gated — expect a pending approval, not instant effect. Record every field set in
   the lockfile. v1: `container_config` JSON column (example
   `config-examples/mount-allowlist.json`).

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
- Reference store: `{store: nanoclaw-env, key: <ENV_VAR>}` — resolve = read that variable
  from the checkout `.env`. v1 has `.env` only.
- v2 optional OneCLI Agent Vault (`/init-onecli`): an HTTPS-proxy gateway injects real
  Authorization headers in-flight, so raw keys never enter agent containers; stub files
  literally contain `onecli-managed` — never "fix" them. Opt out with
  `/use-native-credential-proxy`; env `ONECLI_URL`/`ONECLI_API_KEY`; egress lockdown via
  `NANOCLAW_EGRESS_LOCKDOWN`/`NANOCLAW_EGRESS_NETWORK`. OneCLI-managed values are
  gateway-injected and never resolvable, so it is not usable as an aos reference store —
  capability secret references stay `{store: nanoclaw-env, key: <ENV_VAR>}` either way.
- There is no MCP get-secret tool — never write a prompt that assumes an agent can fetch a
  secret by name.

## Removal

Drive everything from the lockfile entry, in order:

1. Tasks: v2 `ncl tasks cancel --id <series>` (keeps history) or `ncl tasks delete
   --id <series>` per `schedules_owned` id (`pause|resume` for temporary stops); v1: ask the
   main agent to remove the task, then verify the `scheduled_tasks` row is gone.
2. Skills: run the sibling `REMOVE.md` first (v2), then delete the
   `.claude/skills/<installed-name>` symlink; the render dirs in `<home>/personal` are
   deleted via a commit (contract). The `<home>/personal` mount stays if any other aos
   capability is installed in the group.
3. Context blocks: strip the `<!-- aos:<capability>… -->` marker blocks from v2
   `instructions.prepend.md` (then `ncl groups restart`) / v1 `groups/<f>/CLAUDE.md`.
4. Config: v2 `ncl groups config remove-mcp-server|remove-package|remove-mount` per recorded
   field.
5. `.env` lines added at install: remove after asking the user.
6. Groups created by this capability and used by nothing else: v2 `ncl groups delete
   --id <id>` (cascades wirings, config, sessions); orphaned plumbing via
   `ncl wirings delete` and `ncl messaging-groups delete`. v1: the main agent's remove-group
   (deletes the DB row + `groups/<folder>/`).
7. Remove the lockfile entry; verify per the contract (re-run Introspection).

Whole-harness uninstall (not per-capability): v2 `bash nanoclaw.sh --uninstall` (`--dry-run`,
`--yes`); leftover containers
`docker ps -aq --filter label=nanoclaw-install=<slug> | xargs -r docker rm -f`. v1 has no
uninstall script — manual cleanup plus stopping the `launchd/` service.

## Feature notes

| `depends.host` | status | notes / when absent |
|---|---|---|
| `cron` | ✓ both | DB-sweep tasks, ±60 s + container cold start — not OS cron; v1 also interval/once kinds |
| `messaging.inbound` | ✓ both | adapter → router → container; v2 adds attachments, mentions, question cards |
| `messaging.outbound` | ✓ both | v2 MCP tools `send_message`, `send_file`, `edit_message`, `add_reaction`, `send_card`, `ask_user_question` — send-only, no read-messages tool; v1 verified only `send_message` |
| `voice.stt` | v2 ✗ · v1 ⚠ | v1 installable `/add-voice-transcription` (absent from the v2 catalog); absent ⇒ apply the schedule's declared degraded mode |
| `voice.tts` | ✗ both | apply the declared degraded mode |
| `calendar.read` / `calendar.write` | v2 ⚠ · v1 ✗ | v2 installable `/add-gcal-tool` (Google Calendar MCP tool); absent ⇒ degraded mode |
| `email` | ⚠ both | v2 `/add-gmail-tool` (read/search/send/label/draft) + `/add-resend` outbound channel; v1 `add-gmail` skill; absent ⇒ degraded mode |
| `secrets-store` | v2 ✓ · v1 ⚠ | `.env` always; v2 optionally the OneCLI vault; v1 `.env` only |

Degraded-mode wiring: `manual` ⇒ the invocable skill lands in
`.claude/skills/` scoped (v2 `skills` field) to the group that would have owned the job;
`inline` ⇒ no verified task-edit verb exists — cancel the owning task and recreate it under
the same `aos:` name with the appended prompt.

Channels beyond built-in `cli` are all installable slash-skills: WhatsApp (Baileys + Cloud
API), Telegram, Discord, Slack, Signal, iMessage, Teams, Google Chat, GitHub, Linear,
Matrix, Webex, WeChat, Delta Chat, Emacs, Resend. The v1 set was smaller: WhatsApp
(flagship), Telegram, Discord, Slack, Gmail — WhatsApp auth is `npm run auth` (QR).
