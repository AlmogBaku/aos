---
harness: hermes
status: verified
source: "hermes 6e7b83a (2026-10-13); live e2e 2026-10-12; session rows probed 2026-10-20"
rules:
  - never hand-edit config.yaml or cron/jobs.json — every change goes through the hermes CLI
files: [SOUL.md, AGENTS.md, CLAUDE.md, .cursorrules, memories/MEMORY.md, memories/USER.md,
        skills/*/SKILL.md, cron/jobs.json, config.yaml, .env, mcp.json, hooks/]
mapping:
  agent:
    primitive: profile — a full parallel HERMES_HOME (own config.yaml, .env, SOUL.md, skills/, cron/)
    where: ~/.hermes/profiles/<name>/
    create: hermes profile create <name>
  main:
    primitive: the default profile
    where: ~/.hermes/
  skill:
    primitive: Agent Skills folder — a symlink to the pinned render
    where: {main: ~/.hermes/skills/<installed>, agent: ~/.hermes/profiles/<agent>/skills/<installed>}
  cron:
    primitive: cron job owned by exactly one profile (by directory, not a field)
    where: <profile home>/cron/jobs.json — read freely, write never
    create: hermes -p <profile> cron create '<expr>' '<prompt>' --name 'aos:<cap>:<id>'
    exec: hermes -p <profile> cron create '<expr>' --script '<command>' --no-agent --name 'aos:<cap>:<id>'
    edit: hermes -p <profile> cron edit <id>
  context_block:
    primitive: SOUL.md (identity) · workspace/AGENTS.md (working-dir instructions)
    where: the profile dir
  secret:
    primitive: .env line
    where: {main: ~/.hermes/.env, agent: ~/.hermes/profiles/<agent>/.env}
    store: hermes-env
  config:
    primitive: dotted key in the profile config.yaml
    set: hermes -p <profile> config set <key> <value>
  hook:
    primitive: "shell hook — a hooks: entry in the profile config.yaml"
    consent: one approvals entry (event, command) in the profile's shell-hooks-allowlist.json
    check: hermes -p <profile> hooks doctor
    revoke: hermes -p <profile> hooks revoke <command>
  session:
    primitive: a titled session in the profile's state.db
    open: hermes -p <profile> --cli <skills> chat --in <workdir> -c <title> --create-if-missing --source cli -Q --query-file <file>
    skill_arg: --skills <name>
    continue: hermes -p <profile> chat --resume <session_id> -Q --query-file <file>
    id: {stderr: '^session_id: (\S+)$'}
    missing: {stderr: '^Session not found'}
    busy: {stderr: '^hermes-refusal-reason: SESSION_NOT_OWNED'}
    scrub_env: [HERMES_SESSION_*, HERMES_CRON_SESSION, HERMES_UI_SESSION_ID, HERMES_CRON_AUTO_DELIVER_*]
    branch: {support: none, instead: continue in place and say so}
  plan_mode:
    support: none
    instead: prompt-enforced — declare "planning — no writes until approval" and hold it; the diff gate is the exit
  messaging.inbound:
    primitive: WhatsApp, Slack, Telegram, Discord, Signal, Mattermost, Matrix — bound to a profile via profile_routes + gateway.multiplex_profiles true
  messaging.outbound:
    primitive: cron --deliver origin|local|<platform>:<chat_id>; the messaging toolset; hermes send --to <target>
  voice.stt: {primitive: the stt / voice config sections}
  voice.tts: {primitive: the tts / voice config sections}
  calendar.read: {support: via, via: a calendar skill (check `hermes skills list`)}
  calendar.write: {support: via, via: a calendar skill}
  email: {support: via, via: an email skill}
---
# Hermes cheat-sheet

## Contents

- Primitive mapping
- Materialization guide
- Introspection guide
- Secrets
- Removal
- Feature notes


Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
Hermes. The aos half is the `capability-lifecycle` entry skill's install contract; this
sheet is only the Hermes half.

**Rule zero** (`rules`): both files are machine-rewritten — comments don't survive, and
`jobs.json` holds live scheduler state — so every mutation goes through the `hermes` CLI.


## Primitive mapping

The frontmatter's `mapping` is the glossary: each aos concept and each `depends.host` word →
the Hermes primitive, where it lives, and the one command a template can hold. What follows is
the judgment the rows cannot carry.

- **Agent** (`mapping.agent`): target a profile with `hermes -p <name> …`. Adopt an existing
  profile instead of creating one when it is evidently this capability's (contract).
- **Skill** (`mapping.skill`): per-profile links are how `used_by` scoping works, and a `uses`
  grant is one more link into the grantee's `profiles/<p>/skills/`; a profile sees only its own
  skills dir. Hermes follows symlinks in skills dirs. Name gate: one `--harness-skills` per dir
  (the flag repeats).
- **Session branch** (`mapping.session.branch`): `hermes sessions` has no fork; `--resume` and
  `--continue` reopen a session, never copy one — {{skill: build}} continues in place and says so.
- **Session** (`mapping.session`): `chat -c <title> --create-if-missing` reopens a title that
  exists, so a caller that wants a new session puts the time in the title. A session created from
  the CLI carries no read watermark and counts as read; a continued session that was read turns
  unread. While a turn runs, a second writer is refused (`mapping.session.busy`).
- **Files** (`files`): anything else you write is inert. Do not invent filenames (no
  `persona.md`); persona content goes in `SOUL.md`.

`model_class` mapping: only set `hermes -p <name> config set model.default <model>` when
the profile's default doesn't already fit the class; never hardcode provider names.

## Materialization guide

1. **Agents → profiles.** `hermes profile create <name>`; then inside the profile:
   `purpose` + persona content → `SOUL.md` (replace the seeded default, never leave it
   empty) and record that `SOUL.md` as an `--artifact` — that record is what marks the
   profile as created by this capability; `context_files` → workspace, referenced from
   `workspace/AGENTS.md`; `workspace: shared` → skip profile creation, wire into the
   default profile. **Profile already there** with positive evidence it is this
   capability's (contract: its entry, its skill links or `aos:<capability>:` jobs) → adopt it:
   no `profile create`, no `SOUL.md` write, keep its `state.db`, sessions, gateway,
   workspace and hand-written identity files; record no `SOUL.md`.
   **Background-only agent** (nobody chats with it — an archiver, a steward; its `purpose`
   says it never messages anyone or only runs on schedule) → hide it from the Desktop bots
   roster: in the profile's `profile.yaml` set `ui_meta.hermes-bots.hidden: true`, merging
   into any existing `ui_meta`, and increment `_ui_meta_revisions.hermes-bots` (start at 1).
   An agent a person talks to stays visible. Adopting a profile never changes its visibility.
2. **Skills**: `aos-cap skills <cap-dir>` gives the installed name; the render lives once
   at `<aos_home>/personal/<render-path>/skills/<installed-name>/` (contract);
   create a symlink per `used_by` — `ln -s <render-dir> ~/.hermes/skills/<installed-name>`
   (main) or into `profiles/<p>/skills/`. Never copy. Record each link with
   `aos-cap record … --link <linkpath>`. Per `uses` row (`aos-cap manifest`): `ln -s
   <provider's recorded render dir> ~/.hermes/profiles/<agent>/skills/<installed_name>` for
   each listed agent, recorded with `--uses-link` on **this** capability's entry. Enumerate what is already there for the name gate
   with `hermes skills list` (`-p <profile>` per profile), or the dirs themselves:
   `~/.hermes/skills` and `~/.hermes/profiles/*/skills`.
3. **Cron jobs** (`mapping.cron`). Agent-type entries (`agent` + `prompt_ref`):

   ```
   hermes -p <agent-profile> cron create '<expr>' "<personalized prompt_ref content>" \
     --name 'aos:<capability>:<cron-id>' [--skill <installed-name> …] [--deliver <target>]
   ```

   (`main` ⇒ no `-p`.) **Exec-type entries (`exec:`)** are script-only jobs — hosted by the profile that owns the capability's other cron jobs (the front profile when it declares no agent), no agent,
   no LLM: materialize with Hermes's script job form
   (`mapping.cron.exec`; if this Hermes build lacks
   script jobs, a system crontab line with the same command and a `# aos:<cap>:<id>`
   comment is the fallback — record whichever was used in the lockfile). A path-form exec
   runs as `uv run <aos_home>/upstream/<path-and-args>` (personal capabilities:
   `<aos_home>/personal/…`). Optionally compose surfacing:
   `… || hermes send --to <target> …`. Never write an `origin:` field into jobs.json (Hermes uses it
   for chat provenance). Single-owner check = `hermes cron list` across profiles.
4. **Context blocks** → marker-delimited appends to `SOUL.md` / `workspace/AGENTS.md`.
5. **Config keys**: `hermes config set <dotted.key> <value>` (`-p <profile>` for profile
   config). Verify the key exists first with `hermes config get` — a typo'd key silently
   does nothing. Record every key set in the lockfile.
6. **Native code** (`adapters/hermes/plugins/`): hooks → profile `hooks/`; standalone
   programs stay standalone; `--script` files → the owning profile's `scripts/`
   (`~/.hermes/scripts/` for `main`) — Hermes 0.21 refuses a path outside it.
7. **Shell hooks** (`hooks:` in the profile `config.yaml`): Hermes runs one only after
   it is approved, and a desktop, dashboard or cron session cannot prompt, so it skips an
   unapproved hook with a log warning — `fail_closed` included. Approve each by its exact
   command: one `approvals` entry (`event`, `command`) in the profile's
   `shell-hooks-allowlist.json`, or a TTY prompt. Never `hooks_auto_accept` or
   `--accept-hooks`: both approve every hook the config holds. Then
   `hermes -p <profile> hooks list` must show each hook allowlisted and
   `hermes -p <profile> hooks doctor` must pass. Approval keys on the command string, not
   the script, so after an upgrade rewrites a hook script, doctor's mtime drift is the
   signal to re-check it. Removal revokes it (Removal, step 7).

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

1. Cron jobs: `hermes -p <profile> cron remove <id>` per `cron_owned` id; then
   delete leftover `cron/output/<id>*`.
2. Skills: delete every symlink the entry's `links` and `uses_links` list; then delete the
   render dirs in `<aos_home>/personal/<render-path>/skills/` via a commit (revertible — the
   persist hook's message says why). Never `capabilities/<id>/` of the user's own package:
   that is its source.
3. Context blocks: strip the `<!-- aos:<capability>… -->` marker blocks.
4. Config keys: `hermes config unset <key>` per recorded key.
5. `.env` lines added at install: remove after asking the user.
6. Profiles this capability created (its entry records their `SOUL.md`) and used by
   nothing else: `hermes profile delete <name>`. An adopted profile is never deleted —
   no recorded `SOUL.md` means ask.
7. Shell hooks: `hermes -p <profile> hooks revoke <command>` per hook the entry
   installed — before its script goes.
8. Recorded `scripts/` and `hooks/` files of each profile: delete.
9. Remove the lockfile entry; verify per the contract (re-run Introspection).

## Feature notes

The `depends.host` rows of `mapping` answer which features exist here. `calendar.*` and `email`
are present only when a skill provides them (`hermes skills list`); absent ⇒ apply the cron
job's `degraded:` mode. Inbound channels need `profile_routes` and `gateway.multiplex_profiles:
true` to reach an agent profile.

Degraded-mode wiring: `manual` ⇒ the invocable skill lands at `mapping.skill.where.agent` of
the profile the job would have owned; `inline` ⇒ `mapping.cron.edit`.

Safety rails to route through: the `personal/` git history first (renders and MOD files —
revert = rollback), then Hermes-native: `hermes backup --quick` (pre-install),
`state-snapshots/` (pre-update), `hermes doctor`, `hermes skills diff` (feeds the §3.3
round-trip; note stock-vs-modified tracking sees through links to the render),
`hermes profile export` (before risky surgery).

Native seam note: Hermes has its own distribution mechanism (`hermes profile install
<git-url>` + `distribution.yaml`, distribution-owned vs user-owned paths, `local/`
namespace). A one-agent capability could ship its Hermes adapter as a distribution;
v0.1 materializes directly.
