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

**Rule zero: never hand-edit `<workspace>/cron/jobs.json`, `memory/`, or the config dir's
`sessions/`.** Jobs are live scheduler state, mutated only through the agent's `cron` tool
or the WebUI Automations view; `memory/` belongs to Dream. There is no `config set` CLI:
`config.json` is edited as a JSON merge into the existing file — never a replacement —
through the diff gate, checked with `nanobot status`, applied by a gateway restart. Nanobot
rewrites `config.json` itself (camelCase keys), so re-read it before every merge.


## Primitive mapping

An instance is one `config.json` (default `~/.nanobot/config.json`) plus its agent
workspace (default `~/.nanobot/workspace/`); `<workspace>` below means that directory.

| aos concept | Nanobot primitive | Where / how |
|---|---|---|
| agent | **instance** — its own config, workspace and gateway | `nanobot onboard --config ~/.nanobot-<name>/config.json --workspace ~/.nanobot-<name>/workspace`, then the same `--config` on every later command. One agent per instance: `agents.defaults` is the only agent block, and `spawn` subagents are task workers, not personas |
| front agent (`main`) | the default instance | `~/.nanobot/config.json` + `~/.nanobot/workspace/` |
| skill | Agent Skills folder `<workspace>/skills/<installed-name>/SKILL.md` — a **symlink** to the pinned render in `<aos_home>/personal` | the dir name is the identity (no flat `<name>.md` form); the loader follows symlinked dirs. Precedence workspace > Agent Plugin > built-in, and a workspace skill **silently shadows** a same-named one. Loading is progressive: the prompt lists name + description, the model `read_file`s the body, `$<name>` in a message forces it in. **Read wall**: `tools.restrictToWorkspace: true` or any `tools.exec.sandbox` makes `read_file` resolve the link and refuse a target outside the workspace — check both before linking; if either is on, stop and say so (never fall back to copying) |
| schedule | session-bound cron job in `<workspace>/cron/jobs.json` | created only by the agent's `cron` tool from inside a chat session — no CLI. Fires as a turn in that session, and only while `nanobot gateway` runs |
| context block | bootstrap files, re-read every turn | `AGENTS.md` (instructions, read from the project root — a WebUI chat with another project selected reads that project's instead), `SOUL.md` (voice, persona), `USER.md` (the user). Dream edits `SOUL.md`, `USER.md` and `memory/MEMORY.md`; it never touches `AGENTS.md` |
| secret | a variable in the gateway's process environment, referenced as `${VAR}` in `config.json` | see Secrets |
| plan mode | none native — prompt-enforced (the TUI/WebUI access selector is default vs full, not read-only) | declare "planning — no writes until approval" and hold it; the diff gate is the exit |
| session branch | TUI only — `/branch` in the native terminal UI forks a saved conversation from a completed reply; `/sessions` switches back | {{skill: build}}'s branch step: `/branch`; back: `/sessions`. Reload: skills and bootstrap files are re-read every turn, so new ones show on the next message; `config.json` changes need a gateway restart. From `docs/cli-reference.md`; unverified in a live session |

Files Nanobot consumes — anything else you write is inert: workspace `AGENTS.md`,
`SOUL.md`, `USER.md`, `HEARTBEAT.md` (tasks under `## Active Tasks`), `memory/MEMORY.md` +
`memory/history.jsonl` (Dream's), `prompts/dream.md`, `prompts/evaluator.md`,
`skills/*/SKILL.md`, `plugins/*/` (`plugin.json`, `mcp.json`, `skills/`), `cron/jobs.json`,
`triggers/`; in the config dir, `config.json`, `sessions/`, `auth/mcp.json`, `plugin-data/`.
No `TOOLS.md`, `IDENTITY.md`, `CLAUDE.md` or `.env` is read — never invent filenames.

`model_class` mapping: only add a `modelPresets.<preset>` entry and point
`agents.defaults.modelPreset` at it when the instance's default doesn't already fit the
class; never hardcode provider names.

## Materialization guide

Config edits apply on a gateway restart: `nanobot gateway restart` (background), the
service manager (`gateway install-service`), or a rerun in its terminal (foreground).

1. **Agents → instances.** `nanobot onboard --config … --workspace …` per the mapping row;
   never rerun bare `onboard` on an existing config (it offers to overwrite — `--refresh` is
   the safe form). The new config has no provider: set one as the default instance does
   (`${VAR}`, never inline keys) until `nanobot status --config …` reports ready, and give it
   its own `gateway.port` and `channels.websocket.port`. `purpose` + persona content →
   `SOUL.md` (replace the seeded default, never leave it empty) and record that `SOUL.md` as
   an `--artifact` — the record that marks the instance as created by this capability. Dream
   edits `SOUL.md`, so drift on that artifact is expected (`/dream-log` says why).
   `workspace: shared` → no new instance; wire into the default one. **Instance already
   there** with positive evidence it is this capability's (contract) → adopt it: no
   `onboard`, no `SOUL.md` write, keep its sessions, memory and workspace.
2. **Skills**: `aos-cap skills <cap-dir>` gives the installed name; the render lives once
   at `<aos_home>/personal/<render-path>/skills/<installed-name>/` (contract); per `used_by`,
   `ln -s <render-dir> <workspace>/skills/<installed-name>` in that agent's instance. Never
   copy. Record each link with `aos-cap record … --link <linkpath>`; a `uses` grant is one
   more link into the grantee's `skills/`, recorded with `--uses-link`. Name gate: pass
   `<workspace>/skills` and the package's built-in `nanobot/skills/` to `--harness-skills`
   (built-ins at the pin: `clawhub cron github image-generation memory my skill-creator
   summarize tmux update-setup weather`). Never route aos skills through WebUI Skills →
   Discover, the `clawhub` skill, or an Agent Plugin — the pinned render is the source.
3. **Tools.** The shell `exec` tool starts with a bare environment (`HOME`, `LANG`, `TERM`):
   a tool the briefing puts on PATH needs its absolute bin dir in `tools.exec.pathPrepend`
   (no `~` expansion), and under `tools.exec.sandbox` in `tools.exec.sandboxRoBinds` too.
   MCP servers → `tools.mcpServers.<name>`: stdio `{command, args, env, cwd}` or HTTP
   `{url, headers}`; their tools appear as `mcp_<server>_<tool>` (`enabledTools` narrows).
4. **Schedules.** Agent-type entries (`agent` + `prompt_ref`): from a chat session of the
   owning instance — the WebUI/TUI topic or chat that should receive each run — call:

   ```
   cron(action="add", name="aos:<capability>:<schedule-id>",
        message="<personalized prompt_ref content>", cron_expr="<cron>", tz="<IANA>")
   ```

   `every_seconds=<n>` / `at="<iso>"` for interval/one-shot kinds (one-shots delete
   themselves). The message runs as a turn in that session, so it must be self-contained;
   record the returned id under `schedules_owned`. Single-owner check =
   `cron(action="list")` in every instance first. **Exec-type entries (`exec:`)** have no
   native form — every user job is an agent turn — so materialize a system crontab line
   with the same command and a `# aos:<cap>:<id>` comment, recorded in the lockfile; a
   path-form exec runs as `uv run <aos_home>/upstream/<path-and-args>` (personal capabilities:
   `<aos_home>/personal/…`). Optional surfacing: `… || nanobot trigger <trigger-id> "<msg>"`,
   the trigger made once by `/trigger <name>` in the target chat. Check `nanobot gateway
   status` first — jobs never fire while the gateway is down.
5. **Context blocks** → marker-delimited appends to `AGENTS.md` in the owning instance's
   workspace; direct file edits are correct here (no CLI). Not `SOUL.md`/`USER.md`: Dream
   rewrites those and may reword text inside the markers.
6. **Config keys**: a JSON merge into the instance's `config.json`, secrets only as
   `${VAR}`; `nanobot status --config …`, then restart the gateway. Record every key path
   set in the lockfile (`tools.mcpServers.<name>`, `tools.exec.pathPrepend`, …).
7. **Hooks.** None a capability can declare: no hook file, config key or approval list. The
   gateway and CLI hard-wire their own `AgentHook`s; SDK hooks run only inside a Python
   program embedding Nanobot (`bot.run(hooks=[…])`). With no consent mechanism there is
   nothing to approve or verify, so a capability that declares a hook stops here — say so,
   and never emulate one with a cron job, `HEARTBEAT.md`, or a `nanobot.tools` entry-point
   package (those load at startup with no gate at all). The one consent gate is Agent
   Plugin activation, with the same trap: a `<workspace>/plugins/` package is inactive until
   enabled in WebUI Apps, the approval keys on a sha256 of its paths, link targets and file
   contents, and any change deletes it with no log line — its skills and MCP servers stop
   loading until re-enabled.

## Introspection guide

- `nanobot --version`; `nanobot status [--config …]` — paths, model, provider keys (set /
  not set), readiness; no model call. `nanobot channels status`; `nanobot plugins list`
  (runtime extras and channel enablement — not Agent Plugins).
- `nanobot gateway status` (PID, mode, clients), `nanobot gateway logs --no-follow`;
  `http://127.0.0.1:18790/health` (WebSocket readiness only).
- In chat: `/skill` (enabled skills), `/status`, the agent's `cron(action="list")` (name,
  id, schedule, last/next run; `dream` and `heartbeat` are protected system jobs).
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
- Reference store: `{store: nanobot-env, key: <ENV_VAR>}` — resolve = that variable in the
  gateway's environment, consumed in config as `${<ENV_VAR>}`; restart after adding one.
- `exec` does not inherit that environment: a variable a shell-run tool needs goes in
  `tools.exec.allowedEnvKeys`; an MCP server gets its own via `tools.mcpServers.<name>.env`.
- Installs never write `auth/mcp.json` (MCP OAuth tokens) or provider OAuth state.

## Removal

There is no uninstall command — drive everything from the lockfile entry, in order:

1. Cron jobs: `cron(action="remove", job_id="<id>")` per `schedules_owned` id, from that
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

| `depends.host` | status | notes |
|---|---|---|
| `cron` | ✓ | `cron` tool: `every`, cron expression + IANA `tz`, one-shot `at`; session-bound, fires only while the gateway runs |
| `messaging.inbound` | ✓ | Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost, Teams, Feishu, DingTalk, WeCom, WeChat, QQ, Email, WebUI and more — `channels.<name>` per instance, access via pairing or `allowFrom` |
| `messaging.outbound` | ✓ | cron runs reply into their origin chat; the `message` tool takes `channel` + `chat_id` for cross-channel sends |
| `voice.stt` | ✓ | `transcription` section (Groq, OpenAI, OpenRouter, …) for voice messages and WebUI mic |
| `voice.tts` | ✗ | none found in source ⇒ apply the schedule's `degraded:` mode |
| `calendar.read` / `calendar.write` | ⚠ via MCP | present only if a calendar server is under `tools.mcpServers`; absent ⇒ degraded mode |
| `email` | ⚠ via channel | the email channel (IMAP poll + SMTP reply; `consentGranted: true` required) or an MCP server; absent ⇒ degraded mode |
| `secrets-store` | ⚠ partial | process environment + `${VAR}`, no vault — treat as env-file-grade |

Degraded-mode wiring: `manual` ⇒ the invocable skill lands in the `skills/` of the
instance that would have owned the job (`$<name>` runs it); `inline` ⇒ the `cron` tool has
no edit verb — remove the target aos-owned job, add it again under the same name with the
appended message, and re-record its new id.

Native seam note: Agent Plugins v1 (`<workspace>/plugins/<name>/`: `plugin.json`, optional
`mcp.json` and `skills/`) are Nanobot's own package boundary for skills plus stdio MCP
servers. But a plugin must be a real directory inside `plugins/` (one resolving elsewhere
is skipped) and any file change deactivates it — at odds with render-plus-symlink
upgrades, so v0.1 materializes directly. Third-party skills (WebUI Skills → Discover, the
`clawhub` skill) land in `skills/`; never install one without the user's explicit OK.

Unverified, confirm on the live system: whether a job created from a one-shot `nanobot
agent -m` session (channel `cli`) delivers anywhere when it fires — create jobs from a
WebUI, TUI or chat session; the `read_file` wall on linked skills
(`nanobot/security/workspace_policy.py`, traced, not run); the bare `exec` environment and
`tools.exec.allowedEnvKeys` (`nanobot/agent/tools/shell.py`; not in
`docs/configuration.md`); that Dream cannot write through a skill link (its write root is
`skills/`, resolved); how Dream treats marker blocks in `SOUL.md`/`USER.md`; which config
changes apply live (v0.3.0 notes say live, `docs/troubleshooting.md` says restart).
