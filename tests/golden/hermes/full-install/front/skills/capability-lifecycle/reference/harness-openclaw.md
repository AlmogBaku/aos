---
harness: openclaw
status: research-drafted
source: "OpenClaw source and docs (post-rename from Clawdbot → Moltbot → OpenClaw, Jan 2026); <DATE> research"
rules:
  - never hand-edit cron/jobs.json or the shared state DB, and drive openclaw.json only through openclaw config set/unset/validate
files: [AGENTS.md, SOUL.md, USER.md, IDENTITY.md, TOOLS.md, HEARTBEAT.md, BOOT.md,
        BOOTSTRAP.md, MEMORY.md, memory/YYYY-MM-DD.md, skills/*/SKILL.md,
        openclaw.json, .env, cron/jobs.json]
mapping:
  agent:
    primitive: agent — id + own workspace + per-agent state
    where: ~/.openclaw/workspace-<name>/
    create: "openclaw agents add <name> --workspace ~/.openclaw/workspace-<name> --non-interactive"
  main:
    primitive: the reserved main agent — cannot be deleted
    where: ~/.openclaw/workspace/
  skill:
    primitive: Agent Skills folder — a symlink to the pinned render in <aos_home>/personal; identity = frontmatter name
    where: {agent: <workspace>/skills/<installed-name>, global: ~/.openclaw/skills/<installed-name>}
  cron:
    primitive: Gateway-hosted cron job — fires only while the Gateway runs; jobs persist
    where: ~/.openclaw/cron/jobs.json — read freely, write never
    create: "openclaw cron add --cron '<expr>' [--tz <IANA>] --message '<prompt_ref>' --agent <agent-id> --session isolated --name 'aos:<capability>:<cron-id>'"
    exec: "openclaw cron add --cron '<expr>' --command '<exec-command>' --name 'aos:<capability>:<cron-id>'"
  context_block:
    primitive: workspace bootstrap files — auto-injected each session
    where: workspace AGENTS.md, SOUL.md, USER.md, IDENTITY.md, TOOLS.md
    note: "sub-agent sessions receive only AGENTS.md + TOOLS.md — capability context for sub-agents goes there; bootstrap files cap at 20k chars each, 60k total"
  secret:
    primitive: .env line (global) or SecretRef in openclaw.json
    where: {global: ~/.openclaw/.env, legacy: ~/.config/openclaw/gateway.env}
    store: openclaw-env
  config:
    primitive: dotted key in openclaw.json (JSON5)
    where: ~/.openclaw/openclaw.json
    set: openclaw config set <dot.path> <value>
  hook:
    primitive: in-process hook — HOOK.md + handler.ts copied into ~/.openclaw/hooks/<name>/
    consent: openclaw hooks enable <name>
    check: "openclaw hooks list --json (loadable, blockedReason)"
    revoke: "openclaw config unset hooks.internal.entries.<name>.enabled; delete ~/.openclaw/hooks/<name>/"
  session:
    support: unknown
    note: "research <DATE>: `openclaw gateway call sessions.create --params '{\"agentId\":…,\"label\":<title>,\"message\":<prompt>}'`; continue via `gateway call sessions.send`; unread via `sessions.patch` (docs/cli/gateway/query.md, packages/gateway-protocol/src/schema/sessions-create.ts)"
  plan_mode:
    support: none
    instead: prompt-enforced — declare "planning — no writes until approval" and hold it; the diff gate is the exit
  calendar.read:
    support: via
    via: gog (Google Workspace CLI) skill
  calendar.write:
    support: via
    via: gog (Google Workspace CLI) skill
  email:
    support: via
    via: gog (Gmail) skill; native Gmail PubSub hooks also available via openclaw webhooks gmail setup
  messaging.inbound:
    primitive: 20+ channels (WhatsApp, Telegram, Slack, Discord, Signal, Matrix, Teams, IRC, …; some plugin-gated); channel→agent binding via --bind
  messaging.outbound:
    primitive: agent message tool; openclaw message send --target …; cron --channel … --to …
  voice.stt:
    primitive: voice-note STT + Talk Mode
  voice.tts:
    primitive: built-in tts tool (~14 providers); native voice messages on Telegram/WhatsApp/Matrix/Feishu
---
# OpenClaw cheat-sheet

## Contents

- Primitive mapping
- Materialization guide
- Introspection guide
- Secrets
- Removal
- Feature notes


Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
OpenClaw. The aos half is the `capability-lifecycle` entry skill's install contract; this
sheet is only the OpenClaw half.

> [!WARNING]
> Research-drafted: no aos e2e install has run on OpenClaw yet (support-matrix honesty,
> ARCHITECTURE §5.3). Verify each mapping against the live install; fix and PR anything
> wrong. The project renamed twice (Clawdbot → Moltbot → OpenClaw, Jan 2026) — legacy
> `clawdbot`/`moltbot` paths and env prefixes may survive in older setups.

**Rule zero** (`rules`): never hand-edit `cron/jobs.json` or the shared state DB, and
drive `openclaw.json` only through `openclaw config set/unset/validate`. The config schema
is strict — one unknown key and the Gateway refuses to start. Everything lives under
`~/.openclaw/` (override: `OPENCLAW_STATE_DIR`); the `config.yaml` path some blogs cite
does not exist — the config file is `openclaw.json` (JSON5).


## Primitive mapping

The frontmatter's `mapping` is the glossary: each aos concept and each `depends.host` word →
the OpenClaw primitive, where it lives, and the one command a template can hold. What
follows is the judgment the rows cannot carry.

- **Agent** (`mapping.agent`): set the agent's identity with
  `openclaw agents set-identity --agent <id> --from-identity` (reads workspace `IDENTITY.md`
  after you write it). `workspace: shared` ⇒ skip creation, wire into `main`.
- **Skill** (`mapping.skill`): OpenClaw takes skill identity from frontmatter, not the
  folder; `description` is required. Skill roots by precedence: `<workspace>/skills` →
  `<workspace>/.agents/skills` → `~/.agents/skills` → `~/.openclaw/skills` (global).
  OpenClaw follows symlinked dirs. Enumerate existing names for the name gate with
  `openclaw skills list --json`, or pass each root dir to `--harness-skills`. `{baseDir}`
  resolves skill-local files. Do not route aos skills through `openclaw skills install` or
  ClawHub — the pinned render in `<aos_home>/personal` is the source.
- **Cron** (`mapping.cron`): Gateway-hosted, fires only while the Gateway runs. Check
  `openclaw gateway status` first — jobs never fire while the Gateway is down. For
  interval/one-shot kinds use `--every <10m|1h|1d>` / `--at <iso>` instead of `--cron`;
  one-shots take `--delete-after-run`.
- **Context block** (`mapping.context_block`): sub-agent sessions receive only `AGENTS.md`
  + `TOOLS.md` — capability context for sub-agents goes there. There is no CLI for context
  blocks; direct file edits are correct. Mind the 20k-per-file / 60k-total caps.
- **Hook** (`mapping.hook`): in-process (`HOOK.md` + `handler.ts`), distinct from
  `hooks.enabled` HTTP webhook ingress. Copy to `~/.openclaw/hooks/<name>/` — not symlink
  (discovery appears to skip non-directory dirents; symlinked render may be ignored — confirm
  on the live system). Approval keys on the name, not the code. Never
  `hooks.internal.enabled: true` alone, `hooks.internal.load.extraDirs`, or
  `plugins install --link` — each opens selection beyond one entry. Files are not watched:
  `openclaw gateway restart` after an upgrade rewrites one.
- **Files** (`files`): no other workspace-root `.md` is read — never invent filenames.

`model_class` mapping: only pass `--model <id>` when the agent's default doesn't already
fit the class; never hardcode provider names.


## Materialization guide

1. **Agents.** `openclaw agents add` per `mapping.agent.create` with
   `--non-interactive`; persona → workspace `SOUL.md`, identity → `IDENTITY.md` then
   `openclaw agents set-identity --agent <id> --from-identity`; `workspace: shared` → skip
   creation, wire into `main`. Channel routing if the capability needs it:
   `--bind <channel[:account]>`.
2. **Skills.** `aos-cap skills <cap-dir>` gives the installed name; the render lives once
   at `<aos_home>/personal/capabilities/<capability>/skills/<installed-name>/` (contract);
   symlink it into the owning agent's `<workspace>/skills/<installed-name>` per `used_by`
   (`~/.openclaw/skills/` only for genuinely every-agent skills), record each link
   (`aos-cap record … --link`).
3. **Cron jobs.** Agent-type entries (`agent` + `prompt_ref`): use `mapping.cron.create`.
   Exec-type entries (`exec:`): use `mapping.cron.exec`. Deliver to a channel:
   `--channel <platform> --to "channel:ID"`. Single-owner check =
   `openclaw cron list --all` before creating.
4. **Context blocks** → marker-delimited appends to the workspace bootstrap files. Direct
   file edits are correct. Anything a sub-agent must see goes in `AGENTS.md` or `TOOLS.md`.
5. **Config keys**: `openclaw config set <dot.path> <value>`, then
   `openclaw config validate`. Hot-reload is hybrid — channels/agents/cron/tools/plugins
   apply live, `gateway.*` (port/auth/TLS) needs a restart. Record every key in the
   lockfile.
6. **Per-skill secrets**: `skills.entries.<name>.apiKey` (SecretRef) or its `.env` map.
   Env injection does **not** reach sandboxed execution — skills must declare needs via
   `metadata.openclaw` `requires: {env: […]}` + `primaryEnv`.
7. **In-process hooks.** Copy to `~/.openclaw/hooks/<name>/` (not symlink), then enable per
   `mapping.hook.consent`. Never `hooks.internal.enabled: true` alone. Confirm the hook's
   actual side effect — `mapping.hook.check` is inventory only. After an upgrade rewrites a
   hook: `openclaw gateway restart`.


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
- Logs: `OPENCLAW_LOG_LEVEL`, `OPENCLAW_DIAGNOSTICS`.


## Secrets

- Values → global `~/.openclaw/.env` (the recommended store; legacy
  `~/.config/openclaw/gateway.env` may exist). Never echo values. Workspace `.env`
  **blocks credential-shaped vars** (`*_API_KEY`, `*_BASE_URL`, `*_ENDPOINT`,
  `OPENCLAW_*`, `CLAWHUB_*`, …) — never target it for secrets.
- Reference store (`mapping.secret.store`): resolve = read the variable via OpenClaw's
  precedence (process env → global `.env` → `env` block in `openclaw.json`).
- In config, prefer indirection over inline values: `${VAR}` substitution (uppercase
  only) or SecretRef objects `{source: env|file|exec, …}`.
- Never expose `OPENCLAW_GATEWAY_TOKEN`, the gateway password, or cron/hooks webhook
  tokens; keep the Gateway bound to `127.0.0.1:18789` or behind an authed proxy.


## Removal

Drive everything from the lockfile entry, in order:

1. Cron jobs: `openclaw cron remove <jobId>` per `cron_owned` id
   (`cron disable <jobId>` to pause instead of delete).
2. Skills: there is **no `skills uninstall` subcommand** — set
   `skills.entries.<name>.enabled: false` via `openclaw config set` and delete the
   symlink from every root the lockfile's `links` list names; the render dirs in
   `<aos_home>/personal` are deleted via a commit (contract).
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

The `depends.host` rows of `mapping` answer which features exist here.
`mapping.calendar.read`, `mapping.calendar.write`, and `mapping.email` are present only when
the respective skill is installed (`openclaw skills list`); absent ⇒ apply the cron job's
`degraded:` mode.

Degraded-mode wiring: `manual` ⇒ the invocable skill lands in
the workspace skills dir of the agent that would have owned the job; `inline` ⇒ no
documented `cron edit` — recreate the target aos-owned job (`cron remove` + `cron add`,
same name) with the appended prompt.

**ClawHub supply-chain caution**: low publishing barrier, documented infostealer incidents.
Never install a third-party skill without `openclaw skills verify @owner/<slug>` and the
user's explicit OK — treat `--acknowledge-clawhub-risk` as a real warning, not a formality.
Prefer `agents.defaults.sandbox.mode: "non-main"`.

Unverified, confirm on the live system: `agents/<agentId>/` leaf layout; the shared
SQLite state DB filename; whether `agents delete` cleans disk; symlinked hook dirs in
`~/.openclaw/hooks/` — discovery (`loadHookEntriesFromDir`) appears to skip non-directory
dirents, so a symlinked render may be ignored; copy, or confirm live.
