# OpenClaw cheat-sheet

Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
OpenClaw. The aos half of the install contract — provenance, lockfile, markers, secret
references, degraded-mode meanings, removal discipline — is the `capability-lifecycle` entry skill's `reference/contract.md`; this sheet
is only the OpenClaw half.

> [!WARNING]
> Research-drafted: no aos e2e install has run on OpenClaw yet (support-matrix honesty,
> ARCHITECTURE §5.3). Verify each mapping against the live install; fix and PR anything
> wrong. The project renamed twice (Clawdbot → Moltbot → OpenClaw, Jan 2026) — legacy
> `clawdbot`/`moltbot` paths and env prefixes may survive in older setups.

**Rule zero: never hand-edit `cron/jobs.json` or the shared state DB, and drive
`openclaw.json` only through `openclaw config set/unset/validate`.** The config schema is
strict — one unknown key and the Gateway refuses to start. Everything lives under
`~/.openclaw/` (override: `OPENCLAW_STATE_DIR`); the `config.yaml` path some blogs cite
does not exist — the config file is `openclaw.json` (JSON5).

## Primitive mapping

| aos concept | OpenClaw primitive | Where / how |
|---|---|---|
| agent | **agent** — id + own workspace + per-agent state | `openclaw agents add <name> --workspace ~/.openclaw/workspace-<name>`; identity via `openclaw agents set-identity --agent <id> --from-identity` (reads workspace `IDENTITY.md`) |
| front agent (`main`) | the reserved `main` agent — cannot be deleted | workspace `~/.openclaw/workspace/` |
| skill | Agent Skills folder; identity = frontmatter `name` (lowercase-hyphen), **not** the folder path | roots by precedence: `<workspace>/skills` → `<workspace>/.agents/skills` → `~/.agents/skills` → `~/.openclaw/skills` (global) — per-workspace dirs are how `used_by` scoping works |
| schedule | Gateway-hosted cron job (fires only while the Gateway runs; jobs persist) | `openclaw cron add …` (see Materialization); store `~/.openclaw/cron/jobs.json` |
| context block | workspace bootstrap files, auto-injected each session | always: `AGENTS.md`, `SOUL.md`, `USER.md`, `IDENTITY.md`, `TOOLS.md`. **Sub-agent sessions get only `AGENTS.md` + `TOOLS.md`** — capability context for sub-agents goes there |
| secret | `~/.openclaw/.env` line (+ SecretRef in config) | see Secrets |

Files OpenClaw consumes — anything else you write is inert: workspace `AGENTS.md`,
`SOUL.md`, `USER.md`, `IDENTITY.md`, `TOOLS.md`; conditionally `HEARTBEAT.md` (heartbeats
on), `BOOT.md` (gateway restart), `BOOTSTRAP.md` (first run only), `MEMORY.md` +
`memory/YYYY-MM-DD.md` (main sessions); `skills/*/SKILL.md` under the roots above (found
≤6 levels deep); `openclaw.json`, `.env`, `cron/jobs.json`. No other workspace-root md is
read — never invent filenames. Bootstrap files cap at 20k chars each, 60k total.

`model_class` mapping: only pass `--model <id>` (on `agents add` or `cron add`) when the
agent's default doesn't already fit the class; never hardcode provider names.

## Materialization guide

Work top-down from `CAPABILITY.md`, under the contract (reference/contract.md).

1. **Agents.** `openclaw agents add <name> --workspace ~/.openclaw/workspace-<name>
   --non-interactive`; persona → the workspace's `SOUL.md`, identity → `IDENTITY.md` then
   `openclaw agents set-identity --agent <id> --from-identity`; `workspace: shared` → skip
   creation, wire into `main`. Channel routing if the capability needs it:
   `--bind <channel[:account]>`.
2. **Skills.** Skills land in the owning agent's `<workspace>/skills/` per `used_by`
   (`~/.openclaw/skills/` only for genuinely every-agent skills); copy/naming rules per
   the contract (reference/contract.md). OpenClaw takes skill identity from frontmatter, not the folder — set the
   materialized copy's `name: <capability>-<id>`; `description` is required. `{baseDir}`
   resolves skill-local files. Do not route aos skills through
   `openclaw skills install`/ClawHub — the clone is the source.
3. **Schedules.** Agent-type entries (`agent` + `prompt_ref`):

   ```
   openclaw cron add --cron '<expr>' [--tz <IANA>] \
     --message "<personalized prompt_ref content>" \
     --agent <agent-id> --session isolated \
     --name 'aos:<capability>:<schedule-id>'
   ```

   `--every <10m|1h|1d>` / `--at <iso>` for interval/one-shot kinds (one-shots:
   `--delete-after-run`). **Exec-type entries (`exec:`)** are native script jobs — use
   `--command "<exec command>"` or `--script <file>` instead of `--message`. Deliver to a
   channel: `--channel <platform> --to "channel:ID"`. Single-owner check =
   `openclaw cron list --all` before creating. Check `openclaw gateway status` first —
   jobs never fire while the Gateway is down.
4. **Context blocks** → marker-delimited appends to the workspace bootstrap files. There
   is no CLI for them; direct file edits are correct here. Anything a sub-agent must see
   goes in `AGENTS.md` or `TOOLS.md` — the only files sub-agent sessions receive. Mind the
   20k-per-file / 60k-total caps.
5. **Config keys**: `openclaw config set <dot.path> <value>`, then
   `openclaw config validate`. Hot-reload is hybrid — channels/agents/cron/tools/plugins apply
   live, `gateway.*` (port/auth/TLS) needs a restart. Record every key in the lockfile.
6. **Per-skill secrets**: `skills.entries.<name>.apiKey` (SecretRef) or its `.env` map.
   Env injection does **not** reach sandboxed execution — skills must declare needs via
   `metadata.openclaw` `requires: {env: […]}` + `primaryEnv`.

## Introspection guide

- `openclaw gateway status`; `openclaw doctor [--fix]`; `openclaw dashboard` (Control UI
  at `http://127.0.0.1:18789/`).
- `openclaw agents list [--bindings] [--json]`.
- `openclaw skills list [--eligible] [--agent <id>] [--json]`; `skills info <name>`;
  `skills check` — debugs missing bins/env/config gates.
- `openclaw cron list [--all]`; `cron get <jobId>`; `cron runs --id <jobId> [--limit N]`.
- `openclaw config get <path>`; `config validate`; `openclaw security audit --deep`.
- Filesystem: `~/.openclaw/skills/`, `workspace*/`, `cron/jobs.json`,
  `agents/<agentId>/` (leaf layout unverified — enumerate, don't assume).
- aos artifacts: `.aos/installs.lock.yaml`, `x-aos-origin:` frontmatter, `aos:` job
  names, `<!-- aos:… -->` markers.
- Logs: `OPENCLAW_LOG_LEVEL`, `OPENCLAW_DIAGNOSTICS`.

## Secrets

- Values → global `~/.openclaw/.env` (the recommended store; legacy
  `~/.config/openclaw/gateway.env` may exist). Never echo values. Workspace `.env`
  **blocks credential-shaped vars** (`*_API_KEY`, `*_BASE_URL`, `*_ENDPOINT`,
  `OPENCLAW_*`, `CLAWHUB_*`, …) — never target it for secrets.
- Reference stores: `{store: openclaw-env, key: <ENV_VAR>}` — resolve = read that
  variable via OpenClaw's precedence (process env → global `.env` → `env` block in
  `openclaw.json`).
- In config, prefer indirection over inline values: `${VAR}` substitution (uppercase
  only) or SecretRef objects `{source: env|file|exec, …}`.
- Never expose `OPENCLAW_GATEWAY_TOKEN`, the gateway password, or cron/hooks webhook
  tokens; keep the Gateway bound to `127.0.0.1:18789` or behind an authed proxy.

## Removal

Drive everything from the lockfile entry, in order:

1. Cron jobs: `openclaw cron remove <jobId>` per `schedules_owned` id
   (`cron disable <jobId>` to pause instead of delete).
2. Skills: there is **no `skills uninstall` subcommand** — set
   `skills.entries.<name>.enabled: false` via `openclaw config set` and/or delete the
   materialized folder from every root the lockfile lists (copies, not links).
3. Context blocks: strip the `<!-- aos:<capability>… -->` marker blocks from the
   bootstrap files.
4. Config keys: `openclaw config unset <key>` per recorded key.
5. `.env` lines added at install: remove after asking the user.
6. Agents created by this capability and used by nothing else:
   `openclaw agents delete <id>` (`main` can never be deleted). Whether this cleans the
   on-disk workspace/agent dir is undocumented — check and delete leftovers per the
   lockfile's recorded paths.
7. Remove the lockfile entry; verify per the contract (re-run Introspection).

## Feature notes

| `depends.host` | status | notes |
|---|---|---|
| `cron` | ✓ | `openclaw cron` (cron exprs, intervals, one-shots, isolated sessions); fires only while the Gateway runs |
| `messaging.inbound` | ✓ | 20+ channels (WhatsApp, Telegram, Slack, Discord, Signal, Matrix, Teams, IRC, …; some plugin-gated); channel→agent binding via `--bind` |
| `messaging.outbound` | ✓ | agent `message` tool; `openclaw message send --target …`; cron `--channel … --to …` |
| `voice.stt` | ✓ | voice-note STT + Talk Mode |
| `voice.tts` | ✓ | built-in `tts` tool (~14 providers); native voice messages on Telegram/WhatsApp/Matrix/Feishu |
| `calendar.read` / `calendar.write` | ⚠ via skill | `gog` (Google Workspace CLI) skill, not built-in; absent ⇒ apply the schedule's `degraded:` mode |
| `email` | ⚠ via skill | `gog` (Gmail) + native Gmail PubSub hooks (`openclaw webhooks gmail setup`); absent ⇒ degraded mode |
| `secrets-store` | ✓ | `.env` + config `env`/SecretRef (OS keyring via `gog`) |

Degraded-mode wiring (meanings in reference/contract.md): `manual` ⇒ the invocable skill lands in
the workspace skills dir of the agent that would have owned the job; `inline` ⇒ no
documented `cron edit` — recreate the target aos-owned job (`cron remove` + `cron add`,
same name) with the appended prompt.

**ClawHub supply-chain caution**: low publishing barrier, documented infostealer
incidents. Never install a third-party skill without `openclaw skills verify
@owner/<slug>` and the user's explicit OK — treat `--acknowledge-clawhub-risk` as a real
warning, not a formality. Prefer `agents.defaults.sandbox.mode: "non-main"`.

Unverified, confirm on the live system: `agents/<agentId>/` leaf layout; the shared
SQLite state DB filename; whether `agents delete` cleans disk.
