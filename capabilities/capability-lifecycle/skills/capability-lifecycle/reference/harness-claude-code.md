---
harness: claude-code
status: research-drafted
source: "code.claude.com/docs; 2026-10-20 research"
rules:
  - the scheduler fires only while the REPL is idle; cron jobs restore on --resume/--continue, not on cold start; one-shot jobs whose time has passed are not restored on resume
files: [CLAUDE.md, AGENTS.md, skills/*/SKILL.md, agents/*.md, commands/*.md, settings.json,
        settings.local.json, .mcp.json, plugins/]
mapping:
  agent:
    primitive: subagent definition file — frontmatter name + description + optional tools + markdown body
    where: ~/.claude/agents/<name>.md
  main:
    primitive: the main conversation — no definition file; give it skills and context blocks instead
    where: ~/.claude/
  skill:
    primitive: Agent Skills folder — a symlink to the pinned render in <aos_home>/personal
    where: {user: ~/.claude/skills/<installed-name>, project: <project>/.claude/skills/<installed-name>}
  cron:
    primitive: CronCreate tool — 5-field cron, local timezone; restores on --resume/--continue not on cold start
    where: .claude/scheduled_tasks.json
    create: "CronCreate(cron_expression='<expr>', prompt='<prompt>', recurring=<bool>)"
    unverified: [persistence semantics, 7-day recurring expiry, Desktop scheduled tasks path]
    note: "research 2026-10-20: no durable parameter; tasks restore on --resume/--continue; one-shot jobs whose time has passed are not restored on resume; backgrounding carries /loop tasks into a bg session; .claude/scheduled_tasks.json documented only with feature-flag fetching off; Desktop scheduled tasks and cloud routines exist for unattended runs (code.claude.com/docs/en/scheduled-tasks)"
  context_block:
    primitive: CLAUDE.md (user or project scope) or AGENTS.md — auto-loaded every session
    where: {user: ~/.claude/CLAUDE.md, project: <project>/CLAUDE.md}
  secret:
    primitive: process environment or env block in settings.json — no dedicated secret store
    where: {env_block: ~/.claude/settings.json, process: shell profile}
    note: "settings.json may be committed if project-scoped — never write secret values into it"
  config:
    primitive: keys in settings.json
    where: {user: ~/.claude/settings.json, local: ~/.claude/settings.local.json, project: <project>/.claude/settings.json}
    set: "write to settings.json directly (no CLI config-set command)"
  hook:
    primitive: hooks entries in settings.json (any scope)
    consent: "add the entry by its exact command via the diff gate — no bulk write"
    check: /hooks in-session or claude --debug
    revoke: remove the entry from settings.json
  session:
    support: unknown
    note: "research 2026-10-20: open via `claude --bg --name <title> <prompt>` (listed in the resume picker as bg; full id via `claude agents --json`); continue via `claude -p --resume <session_id> <prompt>`; `claude -p` sessions are hidden from the picker — not template-shaped yet (code.claude.com/docs/en/sessions, /agent-view, /headless)"
  plan_mode:
    primitive: native (Shift+Tab toggle, or harness starts in it)
  calendar.read:
    support: unknown
  calendar.write:
    support: unknown
  email:
    support: unknown
  messaging.inbound:
    support: unknown
  messaging.outbound:
    support: unknown
  voice.stt:
    support: unknown
  voice.tts:
    support: unknown
---
# Claude Code cheat-sheet

## Contents

- Primitive mapping
- Materialization guide
- Introspection guide
- Secrets
- Removal
- Feature notes


Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
Claude Code (Anthropic's CLI/desktop/IDE coding agent). The aos half is the
`capability-lifecycle` entry skill's install contract; this sheet is only the Claude Code
half.

> [!WARNING]
> Research-drafted: no aos e2e install has run on this harness yet (ARCHITECTURE §5.3).
> Verify each mapping against the running build during install, and fix-and-PR anything that
> turned out wrong. Claude Code ships frequently, so treat a mapping that disagrees with
> what you observe as the sheet being stale, not the harness being wrong.

**Rule zero** (`rules`): the scheduler fires only while the REPL is idle; cron jobs restore
on `--resume`/`--continue`, not on cold start; one-shot jobs whose time has passed are not
restored on resume. The why: `CronCreate` takes a 5-field expression, the prompt, and
whether the job recurs — there is no `durable` parameter. Jobs are written to
`.claude/scheduled_tasks.json` (documented only with feature-flag fetching off) and are
restored when you resume the session; cold starts and unattended runs do not fire them. A
one-shot job whose scheduled time has already passed is silently dropped on resume. The
7-day recurring expiry cited in earlier research is unverified against the current build —
mark any cron job needing long-term persistence as unverified in the install summary and
ask the user to confirm. Backgrounding carries `/loop` tasks into the background session.
For a guarantee stronger than idle-REPL, use Desktop scheduled tasks or cloud routines
(`code.claude.com/docs/en/scheduled-tasks`).


## Primitive mapping

The frontmatter's `mapping` is the glossary: each aos concept and each `depends.host` word →
the Claude Code primitive, where it lives, and the one command a template can hold. What
follows is the judgment the rows cannot carry.

Two scopes, and the choice matters for every row below: **user scope** `~/.claude/`
(all projects) and **project scope** `<project>/.claude/` (one repo, committable). aos
installs to user scope by default — capabilities are the user's, not one repo's — unless the
user asks otherwise.

- **Agent** (`mapping.agent`): the `tools:` frontmatter key restricts tools (confirmed) —
  this is how you enforce "no messaging tools". Whether skills can be scoped per-agent the
  way Hermes's per-agent dirs do is **unverified on this harness**: a skill in
  `~/.claude/skills/` is reachable by the main conversation at minimum. Do not promise
  `used_by` scoping for safety on Claude Code until someone confirms the mechanism and
  updates this row. Invoked by description-match or by name.
- **Skill** (`mapping.skill`): user-scope and project-scope skills share one flat namespace
  and must be globally unique across both plus installed plugins (`plugin:skill`). The name
  gate must check both roots and all installed plugins. Skills are symlink-friendly: the
  folder is read through the link, and `reference/` files travel with it.
- **Session branch** (`mapping.session`): `/branch <name>` copies the conversation into a
  new session and switches into it; the original stays intact. `EnterWorktree`/`--worktree`
  isolate files, not the conversation — do not reach for them to branch a session.
- **Files** (`files`): anything else you write is inert. Do not invent filenames. The slash
  command dir (`commands/`) is not an aos primitive — never materialize skills as commands;
  a command is user-invoked by name and absent from the skill registry.

`model_class` mapping: only set the model when the harness's default doesn't already fit
the class; never hardcode provider names.


## Materialization guide

Nothing here needs a restart — Claude Code picks up skills and context files on the next
session; `/context` shows what is loaded now.

1. **The tool first**, if the capability ships one: `uv tool install --from
   <aos_home>/upstream/capabilities/<id>/tool <package>`. Verify `uv --version` before
   wiring anything that assumes it.
2. **Skills.** `aos-cap skills <cap-dir>` gives each installed name; `aos-cap render`
   writes the render once to
   `<aos_home>/personal/capabilities/<id>/skills/<installed-name>/`, then symlink it to
   `~/.claude/skills/<installed-name>`. Symlink, never copy — a copy silently stops tracking
   the render.
3. **Agents**, if the capability declares any: write `mapping.agent.where` — frontmatter
   `name` + `description` (+ `tools` to restrict), and the agent's prompt body from
   `agents/<name>/*.md`. `workspace: shared` ⇒ no new agent; fold into the main
   conversation.
4. **Cron jobs — wire them with Rule zero's caveats.** `CronCreate` per `mapping.cron.create`
   with the manifest's cron expression (`expr:`), the prompt from `prompt_ref`, and
   `recurring: true` for recurring jobs. Record the returned job id in the lockfile so
   `remove` can `CronDelete` it. Tell the user what they cannot see: the job only fires while
   the app is open and idle, it restores on resume but not on cold start, and one-shot jobs
   whose time has passed are not restored. Where the capability's contract needs a guarantee
   stronger than that, take the declared degrade (`manual` = materialize the prompt as an
   invocable skill and name the trigger in plain words) and say why in the summary.
5. **Context blocks** inside the marker pair, appended to `~/.claude/CLAUDE.md` (or
   `AGENTS.md` if that is what the user keeps). Blank line before, trailing newline after —
   an identity file ending mid-marker corrupts the next capability's append.
6. **Onboarding** last, through {{skill: onboard}}, so the interview's answers reach
   `MOD.md` before anything reads them.
7. **Shell hooks.** Hooks in any settings scope run on the next matching event with no
   consent gate — interactive and `claude -p`/SDK runs alike, and later script edits silently
   too. The diff gate is the only approval: add the entry by its exact command per
   `mapping.hook.consent`, never a bulk write. `"disableAllHooks": true` and
   `allowManagedHooksOnly` in managed settings each disable every hook in scope — if either
   is set, stop and tell the user; never change them. Verify with `mapping.hook.check`.

Order matters for the diff gate: Claude Code shows every write for approval, so batch
related edits rather than dribbling them.


## Introspection guide

- **What is installed:** `aos-cap list` / `aos-cap show <id>` is the authority.
  The harness side is `ls -la ~/.claude/skills/` — symlink targets tell you which
  renders are ours, and a regular directory where a symlink belongs is the drift `verify`
  cares about most.
- **What is loaded right now:** `/context` in-session. A skill absent there is a name or
  frontmatter problem — check that the folder name equals frontmatter `name`.
- **Available skills:** `~/.claude/skills/`, `<project>/.claude/skills/`, and installed
  plugins. Plugin skills appear namespaced (`plugin:skill`).
- **Agents:** `ls ~/.claude/agents/`. No in-session listing verb.
- **Settings in effect:** `~/.claude/settings.json` merged with `settings.local.json`
  merged with project settings; the local file wins. Read all three before concluding a key
  is unset.


## Secrets

**There is no secret store** (`mapping.secret`). The options are the process environment or
an `env` block in `settings.json` — and `settings.json` is a plain file the user may commit
if it is the project-scoped one.

- Never write a secret value into `settings.json`, `CLAUDE.md`, a skill, or `personal/`.
  Values go to the user's own environment; references go to files.
- A capability that requires a secret is installed by telling the user to export it
  (`export FOO_TOKEN=…` in their shell profile), then referencing `$FOO_TOKEN` by name.
- If a capability cannot work without a managed secret store, say so and stop rather than
  inventing a location. That is a `skip` in the install summary, not a workaround.


## Removal

Walk `aos-cap show <id>` backwards; nothing here is inferred from the filesystem.

1. Delete the symlinks under `~/.claude/skills/` that the lockfile records — the links only,
   never the render they point at, until step 6.
2. Delete `mapping.agent.where` for each agent the capability created. Leave agents it
   merely referenced.
3. Remove context blocks by their marker pair, leaving surrounding text untouched.
4. Uninstall the tool if the capability installed one: `uv tool uninstall <package>`.
5. `CronDelete` each job id the lockfile records. A job that is already gone (one-shot
   whose time passed, cold-start loss) is not drift — say so rather than reporting a
   deletion that did not happen.
6. **Last, once nothing else needs to read it**: drop the pinned render under
   `<aos_home>/personal/capabilities/<id>/` and then the lockfile entry
   (`aos-cap remove <id>`). The entry is the list every earlier step walks, so removing it
   first strands whatever has not been undone.

Confirm: `ls ~/.claude/skills/ | grep <prefix>` returns nothing, and `/context` in a fresh
session no longer lists them.


## Feature notes

The `depends.host` rows of `mapping` answer which features exist here.
`mapping.messaging.inbound`, `mapping.messaging.outbound`, `mapping.voice.stt`,
`mapping.voice.tts`, `mapping.calendar.read`, `mapping.calendar.write`, and `mapping.email`
were not established in the research (`support: unknown`); verify against the running build
before relying on them.

- **`mapping.plan_mode`**: native (Shift+Tab or start-in-plan-mode) — the read-only gate is
  enforced by the harness here, not by prose, which is the strongest form of that gate
  across all harnesses.
- **`mapping.hook`**: hooks run on the next matching event with no consent gate — the diff
  gate is the only approval. Neither `"disableAllHooks": true` nor `allowManagedHooksOnly`
  may be changed; if either is set, stop and tell the user.
- **`mapping.agent` `used_by` scoping**: tool restriction (`tools:`) is confirmed; per-agent
  skill scoping is unverified — do not promise it for safety until confirmed.
- **`mapping.session`**: `/branch` is a conversation copy — same cwd, same skills, a new
  session id — which is what {{skill: build}} wants.
- **The diff gate is native**: every write is shown for approval — batch related edits.
- **Two scopes, one namespace** (`mapping.skill`): a user-scope and a project-scope skill
  with the same name collide; the name gate checks both plus installed plugins.
- **No `.aos/` convention of its own**: machine state stays at `<aos_home>/.aos/`.
