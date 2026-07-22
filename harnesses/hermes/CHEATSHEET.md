# Hermes cheat-sheet

Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
Hermes.

**Rule zero: never hand-edit `config.yaml` or `cron/jobs.json`.** Both are
machine-rewritten (comments don't survive; jobs.json holds live scheduler state). Every
mutation goes through the `hermes` CLI.

## Primitive mapping

| aos concept | Hermes primitive | Where / how |
|---|---|---|
| agent | **profile** — a full parallel HERMES_HOME (own `config.yaml`, `.env`, `SOUL.md`, `skills/`, `cron/`) | `~/.hermes/profiles/<name>/`; directory-defined, no registry entry. `hermes profile create <name>`; target with `hermes -p <name> …` |
| front agent (`main`) | the default profile | `~/.hermes/` itself |
| skill | Agent Skills folder | `~/.hermes/skills/` (main) or `profiles/<p>/skills/` — per-profile dirs are how `used_by` scoping works |
| schedule | cron job owned by exactly one profile (mapping is by directory, not a field) | `hermes -p <profile> cron create '<cron>' '<prompt>' --name … --skill …` |
| context block | `SOUL.md` = identity; `workspace/AGENTS.md` = working-dir instructions | inside the profile dir |
| secret | `.env` line | see Secrets |

Files Hermes consumes — anything else you write is inert: `SOUL.md`,
`AGENTS.md`/`CLAUDE.md`/`.cursorrules` (per working dir), `memories/MEMORY.md`,
`memories/USER.md`, `skills/*/SKILL.md`, `cron/jobs.json`, `config.yaml`, `.env`,
`mcp.json`, `hooks/`. Do not invent filenames (no `persona.md`); persona content goes in
`SOUL.md`.

`model_class` mapping: only set `hermes -p <name> config set model.default <model>` when
the profile's default doesn't already fit the class; never hardcode provider names.

## Materialization guide

Work top-down from `CAPABILITY.md`. Every artifact gets provenance, every path a lockfile
line, and the full diff is shown to the user **before** anything lands.

1. **Agents → profiles.** `hermes profile create <name>`; then inside the profile:
   `purpose` + persona content → `SOUL.md` (replace the seeded default, never leave it
   empty); `context_files` → workspace, referenced from `workspace/AGENTS.md`;
   `workspace: shared` → skip profile creation, wire into the default profile.
2. **Skills, scoped by `used_by`.** Copy each `skills/<id>/` folder into the skills dir
   of every profile in its `used_by` — as **`<capability>-<id>/`** (collision-proof;
   frontmatter `name` stays as shipped). Nowhere else. After filling `{{mod: …}}` slots,
   add to the materialized copy's frontmatter:

   ```yaml
   x-aos-origin: <capability>@<version>
   ```

3. **Schedules.**

   ```
   hermes -p <agent-profile> cron create '<cron>' "<personalized prompt_ref content>" \
     --name 'aos:<capability>:<schedule-id>' [--skill <id> …] [--deliver <target>]
   ```

   (`main` ⇒ no `-p`.) Provenance = the `aos:<capability>:<schedule-id>` name prefix +
   the returned job id in the lockfile under `schedules_owned`. Never write an `origin:`
   field into jobs.json (Hermes uses it for chat provenance). Single-owner (§5.5):
   `hermes cron list` across profiles first; existing schedule elsewhere → ask the user
   to reassign, never duplicate.
4. **Context blocks** → marker-delimited appends to `SOUL.md` / `workspace/AGENTS.md`:

   ```
   <!-- aos:<capability>@<version> begin -->
   …
   <!-- aos:<capability>@<version> end -->
   ```

5. **Config keys**: `hermes config set <dotted.key> <value>` (`-p <profile>` for profile
   config). Verify the key exists first with `hermes config get` — a typo'd key silently
   does nothing. Record every key set in the lockfile.
6. **Native code** (`adapters/hermes/plugins/`): hooks → profile `hooks/`; standalone
   programs stay standalone; `--script` files → `~/.hermes/scripts/`.

**Lockfile** (`.aos/installs.lock.yaml` in the user's clone), per capability+harness:
version, every artifact path + sha256, job ids under `schedules_owned`, config keys set.

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
- MOD.md stores references only: `{store: hermes-env, key: <ENV_VAR>}`. Resolve = read
  that variable from the owning profile's `.env`.
- External stores via `hermes secrets` (Bitwarden/1Password) → `{store: hermes-secrets,
  key: …}` if the user opts in.
- Skills needing a variable in sandboxes declare it in SKILL.md
  `required_environment_variables`.

## Removal

Drive everything from the lockfile entry, in order:

1. Cron jobs: `hermes -p <profile> cron remove <id>` per `schedules_owned` id; then
   delete leftover `cron/output/<id>*`.
2. Skills: delete the materialized dir from **every** profile the lockfile lists
   (copies, not links).
3. Context blocks: strip the `<!-- aos:<capability>… -->` marker blocks; never touch text
   outside markers.
4. Config keys: `hermes config unset <key>` per recorded key.
5. `.env` lines added at install: remove after asking the user.
6. Profiles created by this capability and used by nothing else: `hermes profile delete
   <name>`.
7. Recorded `~/.hermes/scripts/` and `hooks/` files: delete.
8. Remove the lockfile entry. **MOD.md is never deleted** (§3.3).

Verify by re-running Introspection: no `aos:<capability>` job names, no
`x-aos-origin: <capability>@`, no marker blocks remain.

## Feature notes

| `depends.host` | status | notes |
|---|---|---|
| `scheduler` | ✓ | `hermes cron` (cron/interval/once) |
| `messaging.inbound` | ✓ | WhatsApp, Slack, Telegram, Discord, Signal, Mattermost, Matrix; channel→agent binding via `profile_routes` + `gateway.multiplex_profiles: true` |
| `messaging.outbound` | ✓ | cron `--deliver origin|local|<platform>:<chat_id>`; agent sends via messaging toolset |
| `voice.stt` / `voice.tts` | ✓ | `stt`/`tts`/`voice` config sections |
| `calendar.read` / `calendar.write` | ⚠ via skill | present only if a calendar skill is installed (`hermes skills list`); absent ⇒ apply the schedule's `degraded:` mode |
| `email` | ⚠ via skill | same as calendar |
| `secrets-store` | ✓ | `.env` (+ optional `hermes secrets`) |

Degraded modes (§5.5): `manual` ⇒ skip the cron job, materialize the prompt as an
invocable skill in the same profile, tell the user how to run it; `inline` ⇒ append the
prompt (inside markers) to an existing aos-owned job via `hermes cron edit`; `skip` ⇒
record in the lockfile so `doctor` reports it.

Safety rails to route through: `hermes backup --quick` (pre-install), `state-snapshots/`
(pre-update), `hermes doctor`, `hermes skills diff` (feeds the §3.3 round-trip),
`hermes profile export` (before risky surgery).

Native seam note: Hermes has its own distribution mechanism (`hermes profile install
<git-url>` + `distribution.yaml`, distribution-owned vs user-owned paths, `local/`
namespace). A one-agent capability could ship its Hermes adapter as a distribution;
v0.1 materializes directly.
