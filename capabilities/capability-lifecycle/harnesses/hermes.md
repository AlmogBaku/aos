# Hermes cheat-sheet

Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
Hermes. The aos half of the install contract — provenance, lockfile, markers, secret
references, degraded-mode meanings, removal discipline — is the `capability-lifecycle` entry skill's `reference/contract.md`; this sheet
is only the Hermes half.

**Rule zero: never hand-edit `config.yaml` or `cron/jobs.json`.** Both are
machine-rewritten (comments don't survive; jobs.json holds live scheduler state). Every
mutation goes through the `hermes` CLI.

## Primitive mapping

| aos concept | Hermes primitive | Where / how |
|---|---|---|
| agent | **profile** — a full parallel HERMES_HOME (own `config.yaml`, `.env`, `SOUL.md`, `skills/`, `cron/`) | `~/.hermes/profiles/<name>/`; directory-defined, no registry entry. `hermes profile create <name>`; target with `hermes -p <name> …` |
| front agent (`main`) | the default profile | `~/.hermes/` itself |
| skill | Agent Skills folder — a **symlink** to the pinned render in `<home>/personal` | link at `~/.hermes/skills/<capability>-<id>` (main) or `profiles/<p>/skills/<capability>-<id>` — per-profile links are how `used_by` scoping works; Hermes follows symlinks in skills dirs |
| schedule | cron job owned by exactly one profile (mapping is by directory, not a field) | `hermes -p <profile> cron create '<cron>' '<prompt>' --name … --skill …` |
| context block | `SOUL.md` = identity; `workspace/AGENTS.md` = working-dir instructions | inside the profile dir |
| secret | `.env` line | see Secrets |
| plan mode | none native — prompt-enforced | declare "planning — no writes until approval" and hold it; the diff gate is the exit |

Files Hermes consumes — anything else you write is inert: `SOUL.md`,
`AGENTS.md`/`CLAUDE.md`/`.cursorrules` (per working dir), `memories/MEMORY.md`,
`memories/USER.md`, `skills/*/SKILL.md`, `cron/jobs.json`, `config.yaml`, `.env`,
`mcp.json`, `hooks/`. Do not invent filenames (no `persona.md`); persona content goes in
`SOUL.md`.

`model_class` mapping: only set `hermes -p <name> config set model.default <model>` when
the profile's default doesn't already fit the class; never hardcode provider names.

## Materialization guide

Work top-down from `CAPABILITY.md`, under the install contract (the `capability-lifecycle` entry skill's `reference/contract.md`).

1. **Agents → profiles.** `hermes profile create <name>`; then inside the profile:
   `purpose` + persona content → `SOUL.md` (replace the seeded default, never leave it
   empty); `context_files` → workspace, referenced from `workspace/AGENTS.md`;
   `workspace: shared` → skip profile creation, wire into the default profile.
2. **Skills**: the render lives once in
   `<home>/personal/capabilities/<capability>/skills/<id>/` (contract); create a symlink
   per `used_by` — `ln -s <render-dir> ~/.hermes/skills/<capability>-<id>` (main) or
   into `profiles/<p>/skills/`. Never copy. Record each link with
   `aos-lock record … --link <linkpath>`.
3. **Schedules.** Agent-type entries (`agent` + `prompt_ref`):

   ```
   hermes -p <agent-profile> cron create '<cron>' "<personalized prompt_ref content>" \
     --name 'aos:<capability>:<schedule-id>' [--skill <id> …] [--deliver <target>]
   ```

   (`main` ⇒ no `-p`.) **Exec-type entries (`exec:`)** are script-only jobs — no agent,
   no LLM: materialize with Hermes's script job form
   (`hermes cron create '<cron>' --script "<exec command>"
   --no-agent --name 'aos:<capability>:<schedule-id>'`; if this Hermes build lacks
   script jobs, a system crontab line with the same command and a `# aos:<cap>:<id>`
   comment is the fallback — record whichever was used in the lockfile). A path-form exec
   runs as `uv run <home>/upstream/<path-and-args>` (personal capabilities:
   `<home>/personal/…`). Optionally compose surfacing:
   `… || hermes notify …`. Never write an `origin:` field into jobs.json (Hermes uses it
   for chat provenance). Single-owner check = `hermes cron list` across profiles.
4. **Context blocks** → marker-delimited appends to `SOUL.md` / `workspace/AGENTS.md`.
5. **Config keys**: `hermes config set <dotted.key> <value>` (`-p <profile>` for profile
   config). Verify the key exists first with `hermes config get` — a typo'd key silently
   does nothing. Record every key set in the lockfile.
6. **Native code** (`adapters/hermes/plugins/`): hooks → profile `hooks/`; standalone
   programs stay standalone; `--script` files → `~/.hermes/scripts/`.

## Introspection guide

- `hermes status` — components, model, keys (masked).
- `hermes profile list` / `show <name>` / `info <name>` (Distribution column = provenance).
- `hermes skills list` (`-p` per profile); `hermes skills list-modified`, `skills diff
  <skill>` — stock-vs-modified tracking.
- `hermes cron list` (`-p` per profile), `hermes cron runs`. Job shape:
  `{jobs: [{id, name, prompt, skills, schedule: {kind, expr…}, deliver, enabled, …}]}` —
  read freely, write never.
- `hermes config show` / `config get <dotted.key>`; `hermes doctor`.
- Filesystem: `~/.hermes/skills/`, `profiles/*/`, `cron/jobs.json`,
  `channel_directory.json`.
- aos artifacts: `.aos/installs.lock.yaml`, `x-aos-origin:` frontmatter, `aos:` job-name
  prefixes, `<!-- aos:… -->` markers.

## Secrets

- Values → `.env` (root for `main`, the profile's for profile-scoped). Never echo values.
- `auth.json` is Hermes's provider-credential state — installs never write it.
- Reference stores: `{store: hermes-env, key: <ENV_VAR>}` — resolve = read that variable
  from the owning profile's `.env`. External stores via `hermes secrets`
  (Bitwarden/1Password) → `{store: hermes-secrets, key: …}` if the user opts in.
- Skills needing a variable in sandboxes declare it in SKILL.md
  `required_environment_variables`.

## Removal

Drive everything from the lockfile entry, in order:

1. Cron jobs: `hermes -p <profile> cron remove <id>` per `schedules_owned` id; then
   delete leftover `cron/output/<id>*`.
2. Skills: delete the symlink from **every** profile the lockfile's `links` list; then
   delete the render dirs in `<home>/personal/capabilities/<capability>/skills/` via a
   commit (revertible — the persist hook's message says why).
3. Context blocks: strip the `<!-- aos:<capability>… -->` marker blocks.
4. Config keys: `hermes config unset <key>` per recorded key.
5. `.env` lines added at install: remove after asking the user.
6. Profiles created by this capability and used by nothing else: `hermes profile delete
   <name>`.
7. Recorded `~/.hermes/scripts/` and `hooks/` files: delete.
8. Remove the lockfile entry; verify per the contract (re-run Introspection).

## Feature notes

| `depends.host` | status | notes |
|---|---|---|
| `cron` | ✓ | `hermes cron` (cron/interval/once kinds) |
| `messaging.inbound` | ✓ | WhatsApp, Slack, Telegram, Discord, Signal, Mattermost, Matrix; channel→agent binding via `profile_routes` + `gateway.multiplex_profiles: true` |
| `messaging.outbound` | ✓ | cron `--deliver origin|local|<platform>:<chat_id>`; agent sends via messaging toolset |
| `voice.stt` / `voice.tts` | ✓ | `stt`/`tts`/`voice` config sections |
| `calendar.read` / `calendar.write` | ⚠ via skill | present only if a calendar skill is installed (`hermes skills list`); absent ⇒ apply the schedule's `degraded:` mode |
| `email` | ⚠ via skill | same as calendar |
| `secrets-store` | ✓ | `.env` (+ optional `hermes secrets`) |

Degraded-mode wiring (meanings in the entry skill's `reference/contract.md`): `manual` ⇒ the invocable skill lands in
the same profile the job would have owned; `inline` ⇒ append via `hermes cron edit`.

Safety rails to route through: the `personal/` git history first (renders and MOD files —
revert = rollback), then Hermes-native: `hermes backup --quick` (pre-install),
`state-snapshots/` (pre-update), `hermes doctor`, `hermes skills diff` (feeds the §3.3
round-trip; note stock-vs-modified tracking sees through links to the render),
`hermes profile export` (before risky surgery).

Native seam note: Hermes has its own distribution mechanism (`hermes profile install
<git-url>` + `distribution.yaml`, distribution-owned vs user-owned paths, `local/`
namespace). A one-agent capability could ship its Hermes adapter as a distribution;
v0.1 materializes directly.
