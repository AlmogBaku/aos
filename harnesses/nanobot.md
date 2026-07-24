# Nanobot cheat-sheet

Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
Nanobot (obot-platform/nanobot, the MCP-host agent runtime). The aos half of the install
contract — provenance, lockfile, markers, secret references, degraded-mode meanings,
removal discipline — is `BOOTSTRAP.md` §0; this sheet is only the Nanobot half.

> [!WARNING]
> Research-drafted: no aos e2e install has run on this harness yet (ARCHITECTURE §5.3).
> Nanobot is ALPHA (v0.0.x; its README warns of significant breaking changes), so verify
> every mapping below against the running build during install — and fix-and-PR anything
> that turned out wrong.

**Rule zero: never hand-edit `nanobot.db`.** It is Nanobot's SQLite state (sessions +
scheduled tasks); schedules exist only there and are mutated only through the runtime
`*ScheduledTask` tools. `nanobot.yaml`, `agents/*.md`, and `nanobot.env` are plain files
you may edit — through the diff gate, then restart `nanobot run` (config loads at
startup; hot-reload is unverified).

## Primitive mapping

The workspace is the first `--config` path (`nanobot run ./my-config/`; default
`.nanobot/`). All paths below are relative to it.

| aos concept | Nanobot primitive | Where / how |
|---|---|---|
| agent | agent definition — `agents/<id>.md` (YAML frontmatter + markdown body = instructions) or an `agents:` entry in `nanobot.yaml` | id = filename sans `.md`; markdown agents override same-named YAML agents. Fields: `name`, `model`, `mcpServers`, `tools`, `agents` (sub-agent delegation), `skills`, `tasks` |
| front agent (`main`) | `agents/main.md` — the auto entrypoint | else `publish.entrypoint`; >1 agent with neither is an error |
| skill | Agent Skills folder: `skills/<name>/SKILL.md` (dir form; overrides flat `skills/<name>.md`) | one shared `skills/` dir; per-agent scoping (`used_by`) via each agent's `skills:` list. Frontmatter `name` must match the dir name (`^[a-z0-9-]+`, 1–64) — rename to `<capability>-<id>` in the copy |
| schedule | DB-backed scheduled task — created at runtime via the `createScheduledTask` tool, never via config files | 5-field cron, timezone-aware; only daily/weekly/monthly/one-time shapes (dom+dow combined is rejected). Firing starts a **new** chat thread with the stored prompt, so prompts must be self-contained. Referenced by `task:///` URI — record it in the lockfile |
| context block | the agent's md body (its `instructions`) | **no auto-loaded context file exists (no CLAUDE.md/AGENTS.md equivalent) — do not invent one.** Append inside aos markers in `agents/<id>.md` |
| secret | `env:` map in `nanobot.yaml` (mark `sensitive: true`); values in `nanobot.env` | `${VAR}` interpolation anywhere in config; see Secrets |

Files Nanobot consumes — anything else you write is inert: `nanobot.yaml`, `agents/*.md`
(`agents/README.md` is ignored), `skills/*/SKILL.md` and flat `skills/*.md`,
`workflows/*/SKILL.md`, `.nanobot/tasks/*`, `nanobot.env`, `nanobot.db`, and the
deprecated `mcp-servers.yaml|json` (don't add one; only one variant is allowed).

## Materialization guide

Work top-down from `CAPABILITY.md`, under the BOOTSTRAP §0 contract. Config edits take
effect on the next `nanobot run` — restart after materializing.

1. **Agents.** Create `agents/<id>.md`: frontmatter `name:` + fields, `purpose` + persona
   → the markdown body. `workspace: shared` ⇒ no new agent; wire into `main.md`. Sub-agent
   delegation is first-class: list child ids under the parent's `agents:`.
2. **Skills** land in the shared `skills/` dir (naming per BOOTSTRAP §0); Nanobot
   requires frontmatter `name:` to match the dir, so update it in the copy, then attach
   to each `used_by` agent via its `skills:` list.
3. **Tools.** Capability-shipped or external tools land under `mcpServers:` in
   `nanobot.yaml` — remote `{url, headers}` or local stdio `{command, args, env, cwd}` —
   then attach via the agent's `mcpServers:`/`tools:` (ref form `mcpServer/toolName`).
4. **Schedules.** With the runtime up, call `createScheduledTask`: 5-field cron + timezone
   + the personalized `prompt_ref` content as a self-contained prompt, named
   `aos:<capability>:<schedule-id>`. Single-owner check = `listScheduledTasks` first.
   Exec-type entries (`exec:`) have no native form on Nanobot: scheduled tasks always
   start an LLM thread, and `mcpServers:` entries are on-demand MCP tools, not cron
   jobs — so the only faithful materialization is a system crontab line with a
   `# aos:<cap>:<id>` comment, recorded in the lockfile (removal step 1 covers it).
5. **Context blocks** → marker-delimited appends to the owning agent's md body.
6. **Secrets/config**: declare under `env:` (`sensitive: true`, `description`), values →
   `nanobot.env`, reference with `${VAR}`.

## Introspection guide

The full CLI surface is only `run`, `call`, `targets`, `sessions` — everything else is
runtime tools or files.

- `nanobot targets` — list agents/tools (verify config parsed as intended).
- `nanobot call TARGET_NAME [INPUT...]` — invoke an agent or tool from the CLI.
- `nanobot sessions` — list sessions (from `nanobot.db`).
- Runtime tools: `listScheduledTasks` (schedules), `searchSkills`.
- Web chat UI on `:8080`; flags `--debug`, `--trace`.
- Filesystem: `nanobot.yaml`, `agents/`, `skills/`, `workflows/`, `nanobot.env`.
- aos artifacts: `.aos/installs.lock.yaml`, `x-aos-origin:` frontmatter, `aos:` task
  names, `<!-- aos:… -->` markers.

## Secrets

- Declare each variable in `nanobot.yaml` `env:` with `sensitive: true` (redacts in logs)
  and a `description`; the value goes in `nanobot.env` (or process env / `--env`). Never
  echo values.
- Reference store: `{store: nanobot-env, key: <ENV_VAR>}` — resolve = that variable from
  the workspace's `nanobot.env`/process env, consumed in config as `${<ENV_VAR>}`.
- No vault exists; `auth:` is Nanobot's MCP-OAuth block — installs don't write it.
- `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` are auto-detected provider keys — leave them alone.

## Removal

There is no uninstall command — drive everything from the lockfile entry, in order:

1. Scheduled tasks: `deleteScheduledTask` per recorded `task:///` URI (crontab-fallback
   lines: delete the `# aos:<cap>:<id>` line).
2. Skills: delete each `skills/<capability>-<id>/` dir (or the `deleteSkill` tool by URI)
   and remove it from every agent's `skills:` list.
3. Context blocks: strip the `<!-- aos:<capability>… -->` marker blocks from agent bodies.
4. `mcpServers:` entries and `env:` declarations added at install: remove from
   `nanobot.yaml`; `nanobot.env` lines: remove after asking the user.
5. Agents created by this capability and used by nothing else: delete `agents/<id>.md`;
   if one was the entrypoint, set a new `agents/main.md` or `publish.entrypoint`.
6. Restart `nanobot run`; remove the lockfile entry; verify per BOOTSTRAP §0 (re-run
   Introspection).

## Feature notes

| `depends.host` | status | notes |
|---|---|---|
| `cron` | ✓ | scheduled-task tools; daily/weekly/monthly/one-time only — a `schedules[]` cron outside those shapes needs its degraded mode |
| `messaging.inbound` | ✗ | web chat UI only today (Slack/SMS/email are roadmap) ⇒ degraded mode |
| `messaging.outbound` | ✗ | same ⇒ degraded mode |
| `voice.stt` | ✗ | ⇒ degraded mode |
| `voice.tts` | ✗ | ⇒ degraded mode |
| `calendar.read` / `calendar.write` | ⚠ via MCP | present only if the user has a calendar MCP server under `mcpServers:`; absent ⇒ degraded mode |
| `email` | ✗ | roadmap ⇒ degraded mode |
| `secrets-store` | ⚠ partial | `env:` + `sensitive:` redaction, no vault — treat as env-file-grade |

Degraded-mode wiring (meanings in BOOTSTRAP §0): `manual` ⇒ the invocable skill lands in
`skills/` attached to the agent that would have owned the task; `inline` ⇒
`updateScheduledTask` appends (inside markers) to an existing aos-owned task's prompt.

Native seam note: MCP servers are Nanobot's core primitive — anything a capability ships
as standalone software is naturally wired as a local stdio `mcpServers:` entry. Built-in
skills (browser-use, python-scripts, scheduled-tasks, workflows) live in the binary; the
skill registry tools need an Obot platform (`OBOT_URL`), but filesystem skills — all aos
needs — work without it.
