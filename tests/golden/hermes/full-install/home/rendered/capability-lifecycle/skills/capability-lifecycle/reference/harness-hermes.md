---
harness: hermes
status: verified
source: "hermes 6e7b83a (<DATE>); live e2e <DATE>; session rows probed <DATE>; mark_unread probed on 69f73ec <DATE>"
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
    primitive: Agent Skills folder — a symlink to the render in <aos_home>/rendered
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
    mark_unread: {http: 'PATCH http://127.0.0.1:8642/p/<profile>/api/sessions/<session_id>', json: {unread: true}, key: API_SERVER_KEY, env_file: 'hermes -p <profile> config env-path'}
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
- Renders migration (capability-lifecycle 0.7.0)
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
  `--continue` reopen a session, never copy one — capability-build continues in place and says so.
- **Session** (`mapping.session`): `chat -c <title> --create-if-missing` reopens a title that
  exists, so a caller that wants a new session puts the time in the title. A session created from
  the CLI carries no read watermark and counts as read; a continued session that was read turns
  unread. While a turn runs, a second writer is refused (`mapping.session.busy`).
- **Session unread** (`mapping.session.mark_unread`): the CLI cannot set read state, so aos-session
  marks each session it opens unread through the API server's per-profile route (default port
  8642). `default` answers with the listener's own key: never add one to `~/.hermes/.env` (the last
  line wins, so a second one rotates every API client's key). A named profile takes only its own
  `API_SERVER_KEY`: for each named profile aos-session opens sessions in, an install or upgrade that
  finds none in its `.env` appends a generated one (32+ random characters, never echoed) and adds
  `--env-line API_SERVER_KEY` to the full `record` of the capability that owns that agent. Never
  replace an existing key. The key opens the profile's whole `/p/<profile>/` API on the loopback
  listener, not only read state. No key, or the API server off: one warning line, the session still
  opens. Once Hermes ships `hermes sessions mark-unread` (NousResearch/hermes-agent#152602) the row
  becomes `hermes -p <profile> sessions mark-unread <session_id>` and the keys go.
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
   **An agent a person talks to** (operator-facing, or a guest or interview agent) also gets
   the AOS UI tools when the default profile registers them, since a profile never inherits
   MCP servers:
   - `hermes -p <profile> config set mcp_servers.aos-ui.url "$(hermes config get mcp_servers.aos-ui.url)"`,
     then `hermes -p <profile> mcp test aos-ui` must list `present_artifact`;
   - the AOS note:
     `hermes -p <profile> config set platform_hints.aos-ui.append "$(hermes config get platform_hints.aos-ui.append)"`.

   Record both keys with `--config-key`. Without them the agent shows files as attachments AOS
   cannot preview. A background-only agent skips this.
   **Standing links — the AOS Agent creator.** A profile whose `profile.yaml` has
   `ui_meta.aos.role: creator` builds Agents for the user behind AOS's New Agent.
   - Installing or upgrading capability-lifecycle links `capability-lifecycle`,
     capability-build, capability-install and capability-onboard into it, plus the
     vendored `skill-creator` when present.
   - Installing or upgrading kb links kb-recall and kb-route.

   Each link is recorded on its provider's entry with `--link`. The creator gets no other
   lifecycle or kb skill, and with no creator profile there is nothing to do.
2. **Skills**: `aos-cap skills <cap-dir>` gives the installed name; the render lives once
   at `<aos_home>/rendered/<capability>/skills/<installed-name>/` (contract: written to
   `rendered/.staging/<capability>/`, put live by `aos-cap swap`);
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
2. Skills: delete every symlink the entry's `links` and `uses_links` list; then the render,
   `<aos_home>/rendered/<capability>/`, goes to the OS trash once its links are gone (`gio trash` / `trash-put`, never `rm -rf`). Never anything under `personal/`: it holds
   the MOD and, for the user's own package, its source.
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

## Renders migration (capability-lifecycle 0.7.0)

The capability-upgrade skill's renders migration, on Hermes:

- **Scan:** `aos-cap migrate rendered --scan ~/.hermes` with `--ignore` for each of
  `sessions`, `request_dump_*`, `cron/output`, `backups`, `*.bak-*`, `cache`,
  `skills/.archive`, `.curator_backups`, `state-snapshots`, `logs`. Those hold transcripts
  and history, not live configuration. A hook's old approval in `shell-hooks-allowlist.json`
  is listed too; its own `hooks revoke` (below) clears it.
- **A shell hook** (`hooks:` in a profile's `config.yaml`) that names an old render path is
  switched without a moment unapproved, because Hermes skips an unapproved hook even when it
  is `fail_closed`. Each switch is its own gate. The migrate plan shows references as
  `path:line` only, so the user has not yet seen what they are consenting to. Before writing
  anything, show the profile, the event, the old and the new exact command (from
  `hermes -p <profile> config get hooks`) and the allowlist entry you will add, and wait for
  the go-ahead. Then:
  1. Approve the new command first: one `approvals` entry in the profile's
     `shell-hooks-allowlist.json` with `event`, `command`, `approved_at` and
     `script_mtime_at_approval` (the script's mtime), so `hooks doctor` can tell a changed
     script.
  2. Switch only the command, in one write:
     `hermes -p <profile> config set hooks.<event>.<index>.command <new path>`. The index is
     dotted. `hooks.<event>[<index>]` writes a bogus key and leaves the hook unchanged.
  3. Compare `hermes -p <profile> config get hooks` before and after. Everything except
     `command` must be identical: `hooks list` does not show `fail_closed`, and a missing one
     reads as false.
  4. `hermes -p <profile> hooks list` shows it allowed, and `hooks doctor` passes.
  5. `hermes -p <profile> hooks revoke <old command>`.
- **Plugins** (`~/.hermes/plugins/*`) load at gateway start. Before `--finish`, restart the
  gateway (`hermes gateway restart`) once its work is idle and with the user's go-ahead. Then
  confirm each plugin actually loaded from its re-pointed link:
  - `hermes [-p <profile>] plugins list` lists it enabled, for the root and every profile
    that enables it;
  - the gateway log shows its load line after the restart, with no load error.

  A gate plugin that fails to load is simply absent, so "no crash line" proves nothing.

## Feature notes

The `depends.host` rows of `mapping` answer which features exist here. `calendar.*` and `email`
are present only when a skill provides them (`hermes skills list`); absent ⇒ apply the cron
job's `degraded:` mode. Inbound channels need `profile_routes` and `gateway.multiplex_profiles:
true` to reach an agent profile.

Degraded-mode wiring: `manual` ⇒ the invocable skill lands at `mapping.skill.where.agent` of
the profile the job would have owned; `inline` ⇒ `mapping.cron.edit`.

Safety rails to route through: the gate before every `aos-cap swap` and the OS trash after
it (renders), the `personal/` git history (MOD files — revert = rollback), then Hermes-native: `hermes backup --quick` (pre-install),
`state-snapshots/` (pre-update), `hermes doctor`, `hermes skills diff` (feeds the §3.3
round-trip; note stock-vs-modified tracking sees through links to the render),
`hermes profile export` (before risky surgery).

Native seam note: Hermes has its own distribution mechanism (`hermes profile install
<git-url>` + `distribution.yaml`, distribution-owned vs user-owned paths, `local/`
namespace). A one-agent capability could ship its Hermes adapter as a distribution;
v0.1 materializes directly.
