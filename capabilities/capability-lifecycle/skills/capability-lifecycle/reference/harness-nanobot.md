---
harness: nanobot
status: research-drafted
source: "HKUDS/nanobot@v0.3.5 (commit 1bb712d)"
rules:
  - never hand-edit <workspace>/cron/jobs.json, memory/, or the config dir's sessions/; config.json is edited as a JSON merge through the diff gate, never a replacement
files: [AGENTS.md, SOUL.md, USER.md, HEARTBEAT.md, memory/MEMORY.md, memory/history.jsonl,
        prompts/dream.md, prompts/evaluator.md, skills/*/SKILL.md, plugins/*/plugin.json,
        plugins/*/mcp.json, plugins/*/skills/, cron/jobs.json, triggers/, config.json,
        sessions/, auth/mcp.json, plugin-data/]
mapping:
  agent:
    primitive: instance — its own config, workspace and gateway
    where: {config: ~/.nanobot-<name>/config.json, workspace: ~/.nanobot-<name>/workspace/}
    create: "nanobot onboard --config ~/.nanobot-<name>/config.json --workspace ~/.nanobot-<name>/workspace"
  main:
    primitive: the default instance
    where: {config: ~/.nanobot/config.json, workspace: ~/.nanobot/workspace/}
  skill:
    primitive: Agent Skills folder — a symlink to the pinned render in <aos_home>/personal; dir name is the identity
    where: <workspace>/skills/<installed-name>/
    note: "read wall: tools.restrictToWorkspace: true or any tools.exec.sandbox makes read_file resolve the link and refuse a target outside the workspace — check both before linking; if either is on, stop and say so (never fall back to copying)"
  cron:
    primitive: session-bound cron job in <workspace>/cron/jobs.json — created by the agent's cron tool from inside a chat session
    where: <workspace>/cron/jobs.json — read freely, write never
    create: "cron(action=\"add\", name=\"aos:<capability>:<cron-id>\", message=\"<prompt_ref>\", cron_expr=\"<expr>\", tz=\"<IANA>\")"
    exec: "system crontab line with # aos:<cap>:<id> comment (no native exec-type form)"
  context_block:
    primitive: workspace bootstrap files re-read every turn — AGENTS.md (instructions), SOUL.md (voice/persona), USER.md (the user)
    where: <workspace>/AGENTS.md — capability context blocks go here; Dream may reword SOUL.md/USER.md
  secret:
    primitive: process environment + ${VAR} references in config.json — no vault, treat as env-file-grade
    where: gateway process environment (mode-600 env file loaded by supervisor or --env-file)
    store: nanobot-env
  config:
    primitive: JSON merge into config.json — never a full replacement
    where: "~/.nanobot[-<name>]/config.json"
    set: "JSON merge patch through the diff gate; nanobot status --config … to verify; restart the gateway"
  hook:
    support: none
    instead: no capability-declarable hook mechanism — the gateway and CLI hard-wire their own hooks; SDK hooks run only in embedded Python programs; a capability that declares a hook stops here
  session:
    support: unknown
    note: "research 2026-10-20: a new chat via the WebSocket protocol ({\"type\":\"new_chat\"}), no public title setter; `nanobot trigger` only continues an existing chat (docs/websocket.md, docs/cli-reference.md)"
  plan_mode:
    support: none
    instead: prompt-enforced — declare "planning — no writes until approval" and hold it; the diff gate is the exit
  calendar.read:
    support: via
    via: a calendar MCP server under tools.mcpServers
  calendar.write:
    support: via
    via: a calendar MCP server under tools.mcpServers
  email:
    support: via
    via: "the email channel (IMAP poll + SMTP reply; consentGranted: true required) or a mail MCP server"
  messaging.inbound:
    primitive: Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost, Teams, Feishu, DingTalk, WeCom, WeChat, QQ, Email, WebUI and more — channels.<name> per instance
  messaging.outbound:
    primitive: cron runs reply into their origin chat; the message tool takes channel + chat_id for cross-channel sends
  voice.stt:
    primitive: transcription section (Groq, OpenAI, OpenRouter, …) for voice messages and WebUI mic
  voice.tts:
    support: none
    note: none found in source
---
# Nanobot cheat-sheet

## Contents

- Primitive mapping
- Materialization guide
- Introspection guide
- Secrets
- Removal
- Feature notes


Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
Nanobot (HKUDS/nanobot, the `nanobot-ai` package — a lightweight self-hosted personal
agent in the same space as OpenClaw). The aos half is the `capability-lifecycle` entry
skill's install contract; this sheet is only the Nanobot half.

> [!WARNING]
> Research-drafted: no aos e2e install has run on this harness yet (ARCHITECTURE §5.3).
> Drafted from source and docs at `HKUDS/nanobot@v0.3.5` (commit `1bb712d`). Nanobot is
> Alpha and releases often, so verify every mapping below against the running build during
> install — and fix-and-PR anything that turned out wrong.

**Rule zero** (`rules`): never hand-edit `<workspace>/cron/jobs.json`, `memory/`, or the
config dir's `sessions/`. Jobs are live scheduler state, mutated only through the agent's
`cron` tool or the WebUI Automations view; `memory/` belongs to Dream. There is no
`config set` CLI: `config.json` is edited as a JSON merge into the existing file — never a
replacement — through the diff gate, checked with `nanobot status`, applied by a gateway
restart. Nanobot rewrites `config.json` itself (camelCase keys), so re-read it before every
merge.


## Primitive mapping

The frontmatter's `mapping` is the glossary: each aos concept and each `depends.host` word →
the Nanobot primitive, where it lives, and the one command a template can hold. What
follows is the judgment the rows cannot carry.

An instance is one `config.json` (default `~/.nanobot/config.json`) plus its agent
workspace (default `~/.nanobot/workspace/`); `<workspace>` below means that directory.

- **Agent** (`mapping.agent`): one agent per instance — `agents.defaults` is the only agent
  block, and `spawn` subagents are task workers, not personas. Never rerun bare `onboard`
  on an existing config; `--refresh` is the safe form. Give the new instance its own
  `gateway.port` and `channels.websocket.port`. Dream edits `SOUL.md`, so drift on that
  artifact is expected (`/dream-log` says why). `workspace: shared` ⇒ no new instance;
  wire into the default one. **Instance already there** with positive evidence it is this
  capability's → adopt it: no `onboard`, no `SOUL.md` write, keep its sessions, memory and
  workspace.
- **Skill** (`mapping.skill`): the dir name is the identity (no flat `<name>.md` form); the
  loader follows symlinked dirs. Precedence: workspace > Agent Plugin > built-in — a
  workspace skill silently shadows a same-named one. Loading is progressive: the prompt
  lists name + description, the model `read_file`s the body, `$<name>` in a message forces
  it in. The read wall at `mapping.skill.note` must be checked before linking.
- **Cron** (`mapping.cron`): session-bound — fires as a turn in that chat session and only
  while `nanobot gateway` runs. Create from inside the owning chat (WebUI, TUI, or chat
  session). Exec-type entries have no native form; use a system crontab fallback per
  `mapping.cron.exec`.
- **Hook** (`mapping.hook`): no capability-declarable mechanism exists. A capability that
  declares a hook stops here. Never emulate one with a cron job, `HEARTBEAT.md`, or a
  `nanobot.tools` entry-point package (those load at startup with no gate). Agent Plugin
  activation is the one consent gate; any file change deactivates it with no log line.
- **Files** (`files`): no `TOOLS.md`, `IDENTITY.md`, `CLAUDE.md` or `.env` is read — never
  invent filenames.

`model_class` mapping: only add a `modelPresets.<preset>` entry and point
`agents.defaults.modelPreset` at it when the instance's default doesn't already fit the
class; never hardcode provider names.


## Materialization guide

Config edits apply on a gateway restart: `nanobot gateway restart` (background), the
service manager (`gateway install-service`), or a rerun in its terminal (foreground).

1. **Agents → instances.** `nanobot onboard` per `mapping.agent.create`; set a provider
   as `${VAR}` (never inline keys) until `nanobot status --config …` reports ready.
   `purpose` + persona content → `SOUL.md` (replace the seeded default, never leave it
   empty) and record that `SOUL.md` as an `--artifact` — the record that marks the instance
   as created by this capability.
2. **Skills**: `aos-cap skills <cap-dir>` gives the installed name; the render lives once
   at `<aos_home>/personal/<render-path>/skills/<installed-name>/` (contract); per `used_by`,
   `ln -s <render-dir> <workspace>/skills/<installed-name>` in that agent's instance. Never
   copy. Record each link with `aos-cap record … --link <linkpath>`; a `uses` grant is one
   more link into the grantee's `skills/`, recorded with `--uses-link`. Name gate: pass
   `<workspace>/skills` and the package's built-in `nanobot/skills/` to `--harness-skills`
   (built-ins at the pin: `clawhub cron github image-generation memory my skill-creator
   summarize tmux update-setup weather`). Never route aos skills through WebUI Skills →
   Discover, the `clawhub` skill, or an Agent Plugin.
3. **Tools.** The shell `exec` tool starts with a bare environment (`HOME`, `LANG`, `TERM`):
   a tool the briefing puts on PATH needs its absolute bin dir in `tools.exec.pathPrepend`
   (no `~` expansion), and under `tools.exec.sandbox` in `tools.exec.sandboxRoBinds` too.
   MCP servers → `tools.mcpServers.<name>`: stdio `{command, args, env, cwd}` or HTTP
   `{url, headers}`; their tools appear as `mcp_<server>_<tool>` (`enabledTools` narrows).
4. **Cron jobs.** Agent-type entries (`agent` + `prompt_ref`): from a chat session of the
   owning instance, call `mapping.cron.create`. `every_seconds=<n>` / `at="<iso>"` for
   interval/one-shot kinds (one-shots delete themselves). The message runs as a turn in that
   session, so it must be self-contained; record the returned id under `cron_owned`.
   Single-owner check = `cron(action="list")` in every instance first. Exec-type entries
   (`exec:`): materialize per `mapping.cron.exec`. Check `nanobot gateway status` first.
   Optional surfacing: `… || nanobot trigger <trigger-id> "<msg>"`, the trigger made once
   by `/trigger <name>` in the target chat.
5. **Context blocks** → marker-delimited appends to `AGENTS.md` in the owning instance's
   workspace; direct file edits are correct (no CLI). Not `SOUL.md`/`USER.md`: Dream
   rewrites those and may reword text inside the markers.
6. **Config keys**: a JSON merge into the instance's `config.json`, secrets only as
   `${VAR}`; `nanobot status --config …`, then restart the gateway. Record every key path
   set in the lockfile (`tools.mcpServers.<name>`, `tools.exec.pathPrepend`, …).
7. **Hooks.** No capability-declarable hook. A capability that declares one stops here per
   `mapping.hook` — never emulate with a cron job, `HEARTBEAT.md`, or a
   `nanobot.tools` entry-point package. Agent Plugin activation (`<workspace>/plugins/`) is
   the one consent gate: approval keys on a sha256 of paths, link targets and file contents,
   and any change deactivates it with no log line.


## Introspection guide

- `nanobot --version`; `nanobot status [--config …]` — paths, model, provider keys (set /
  not set), readiness; no model call. `nanobot channels status`; `nanobot plugins list`
  (runtime extras and channel enablement — not Agent Plugins).
- `nanobot gateway status` (PID, mode, clients), `nanobot gateway logs --no-follow`;
  `http://127.0.0.1:18790/health` (WebSocket readiness only).
- In chat: `/skill` (enabled skills), `/status`, the agent's `cron(action="list")` (name,
  id, cron job schedule, last/next run; `dream` and `heartbeat` are protected system jobs).
- WebUI (`nanobot webui`, `http://127.0.0.1:8765`): Skills → Installed, Automations, Apps.
- Filesystem, read freely: `<workspace>/skills/`, the bootstrap files, `cron/jobs.json`
  (`{version, jobs: [{id, name, enabled, schedule: {kind, expr, tz, …}, payload: {message,
  sessionKey, …}, state}]}` — read, never write), `cron/runs/`; config dir `sessions/`.


## Secrets

- Nanobot reads no env file of its own: values live in the gateway's process environment,
  and `config.json` names them as `${VAR}` in any string value (resolved in memory at
  startup, never written back). An unset reference fails startup naming the field —
  `nanobot status` shows it. Never inline values in `config.json`, never put them inside the
  workspace (the agent's file tools read it), never echo them.
- Values → whatever starts the gateway: a mode-600 env file the supervisor loads
  (`EnvironmentFile=` in the systemd unit — `gateway install-service` writes none, so add
  it), or `--env-file` under Docker.
- Reference store (`mapping.secret.store`): resolve = that variable in the gateway's
  environment, consumed in config as `${<ENV_VAR>}`; restart after adding one.
- `exec` does not inherit that environment: a variable a shell-run tool needs goes in
  `tools.exec.allowedEnvKeys`; an MCP server gets its own via `tools.mcpServers.<name>.env`.
- Installs never write `auth/mcp.json` (MCP OAuth tokens) or provider OAuth state.


## Removal

There is no uninstall command — drive everything from the lockfile entry, in order:

1. Cron jobs: `cron(action="remove", job_id="<id>")` per `cron_owned` id, from that
   instance (or delete in WebUI Automations); crontab-fallback lines: delete the
   `# aos:<cap>:<id>` line.
2. Skills: delete every symlink the entry's `links` and `uses_links` list, and drop the
   names from `agents.defaults.disabledSkills` if listed; the render dirs in
   `<aos_home>/personal/<render-path>/skills/` are deleted via a commit (contract). Never
   `capabilities/<id>/` of the user's own package: that is its source.
3. Context blocks: strip the `<!-- aos:<capability>… -->` marker blocks.
4. Config keys: remove each recorded key path from `config.json` (JSON merge, diff gate).
5. Environment variables added at install: remove after asking the user.
6. Instances this capability created (its entry records their `SOUL.md`) and used by
   nothing else: `nanobot gateway stop --config …` (and `gateway uninstall-service --name
   …` if installed), then delete that config dir and workspace. An adopted instance is
   never deleted — no recorded `SOUL.md` means ask.
7. Restart the gateway; remove the lockfile entry; verify per the contract (re-run
   Introspection).


## Feature notes

The `depends.host` rows of `mapping` answer which features exist here.
`mapping.calendar.read`, `mapping.calendar.write`, and `mapping.email` are present only
when the respective MCP server or channel is configured; absent ⇒ apply the cron job's
`degraded:` mode. `mapping.voice.tts` has no implementation found in source — apply the
declared degraded mode.

Degraded-mode wiring: `manual` ⇒ the invocable skill lands in the `skills/` of the
instance that would have owned the job (`$<name>` runs it); `inline` ⇒ the `cron` tool has
no edit verb — remove the target aos-owned job, add it again under the same name with the
appended message, and re-record its new id.

Native seam note: Agent Plugins v1 (`<workspace>/plugins/<name>/`: `plugin.json`, optional
`mcp.json` and `skills/`) are Nanobot's own package boundary for skills plus stdio MCP
servers. But a plugin must be a real directory inside `plugins/` (one resolving elsewhere
is skipped) and any file change deactivates it — at odds with render-plus-symlink upgrades,
so v0.1 materializes directly. Third-party skills (WebUI Skills → Discover, the `clawhub`
skill) land in `skills/`; never install one without the user's explicit OK.

Unverified, confirm on the live system: whether a cron job created from a one-shot
`nanobot agent -m` session (channel `cli`) delivers anywhere when it fires — create jobs
from a WebUI, TUI or chat session; the `read_file` wall on linked skills
(`nanobot/security/workspace_policy.py`, traced, not run); the bare `exec` environment and
`tools.exec.allowedEnvKeys` (`nanobot/agent/tools/shell.py`; not in
`docs/configuration.md`); that Dream cannot write through a skill link (its write root is
`skills/`, resolved); how Dream treats marker blocks in `SOUL.md`/`USER.md`; which config
changes apply live (v0.3.0 notes say live, `docs/troubleshooting.md` says restart).
