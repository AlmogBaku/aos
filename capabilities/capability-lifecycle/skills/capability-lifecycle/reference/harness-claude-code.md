# Claude Code cheat-sheet

## Contents

- Primitive mapping
- Materialization guide
- Introspection guide
- Secrets
- Removal
- Feature notes


Knowledge for the harness LLM installing, introspecting, or removing aos capabilities on
Claude Code (Anthropic's CLI/desktop/IDE coding agent). The aos half of the install contract
— provenance, lockfile, markers, secret references, degraded-mode meanings, removal
discipline — is the `capability-lifecycle` entry skill's `reference/contract.md`; this sheet
is only the Claude Code half.

> [!WARNING]
> Research-drafted: no aos e2e install has run on this harness yet (ARCHITECTURE §5.3).
> Verify each mapping against the running build during install, and fix-and-PR anything that
> turned out wrong. Claude Code ships frequently, so treat a mapping that disagrees with
> what you observe as the sheet being stale, not the harness being wrong.

**Rule zero: this harness has no scheduler.** There is no cron primitive, so every
`schedules[]` entry hits its declared degraded mode — almost always `manual`. Do not invent
one: a background task is not a schedule (it dies with the session), and a `crontab` entry
would be outside the harness and invisible to `verify` and `remove`. Say plainly in the
install summary which schedules degraded and what the user must run by hand.


## Primitive mapping

Two scopes, and the choice matters for every row below: **user scope** `~/.claude/` (all
projects) and **project scope** `<project>/.claude/` (one repo, and committable). aos
installs to user scope by default — capabilities are the user's, not one repo's — unless the
user asks otherwise.

| aos concept | Claude Code primitive | Where / how |
|---|---|---|
| skill | Agent Skills folder: `skills/<name>/SKILL.md` — a **symlink** to the pinned render in `<home>/personal` | link at `~/.claude/skills/<installed-name>`. The folder name and frontmatter `name` must agree, which they do: `aos-lock render` writes the installed name into both (contract), so the render needs no adjustment |
| agent | subagent definition: `~/.claude/agents/<name>.md` (frontmatter `name`, `description`, optional `tools`, `model` + markdown body = its prompt) | the dir may not exist yet — create it. Invoked by description-match or by name; there is no per-agent skills list, so `used_by` scoping is advisory here (see Feature notes) |
| front agent (`main`) | the main conversation — not a file you create | it has no definition file to write; give it skills and context blocks instead |
| schedule | **none** — no cron primitive exists | every entry degrades (contract): `manual` = materialize the prompt as an invocable skill + tell the user how to run it · `inline`/`skip` per the manifest. Record the degrade in the lockfile and the summary |
| context block | `~/.claude/CLAUDE.md` (user scope) or `<project>/CLAUDE.md`; `AGENTS.md` is read as an equivalent | auto-loaded every session — this is real push-context, so the MARS mode boundary lands here properly. Append inside aos markers only |
| tool on PATH | an ordinary executable | `uv tool install` puts it on PATH like anywhere else; no harness registration needed. Bash is always available |
| secret | environment, or `env` in `~/.claude/settings.json` | see Secrets — there is no dedicated secret store, which constrains what may be installed |
| plan mode | **native** (Shift+Tab, or the harness starts in it) | read-only until the user approves. This satisfies `capability-build`'s read-only gate for real rather than by prose |
| slash command | `~/.claude/commands/<name>.md` | not an aos primitive. Do not materialize skills as commands: a command is user-invoked by name and is absent from the skill registry, so a skill written as a command never triggers on its own |

Files Claude Code consumes — anything else you write is inert: `CLAUDE.md`/`AGENTS.md`,
`skills/*/SKILL.md`, `agents/*.md`, `commands/*.md`, `settings.json` and
`settings.local.json`, `.mcp.json`, and `plugins/` (marketplace-managed).


## Materialization guide

Work top-down from `CAPABILITY.md`, under the install contract (the `capability-lifecycle`
entry skill's `reference/contract.md`). Nothing here needs a restart — Claude Code picks up
skills and context files on the next session, and `/context` shows what is loaded now.

1. **The tool first**, if the capability ships one: `uv tool install --from
   <home>/upstream/capabilities/<id>/tool <package>`. Verify `uv --version` before wiring
   anything that assumes it.
2. **Skills.** `aos-lock skills <cap-dir>` gives each installed name; `aos-lock render`
   writes the render once to
   `<home>/personal/capabilities/<id>/skills/<installed-name>/`, then symlink it to
   `~/.claude/skills/<installed-name>`. Symlink, never copy — a copy silently stops tracking
   the render, so `verify` goes blind and `upgrade` has two truths.
3. **Agents**, if the capability declares any: write
   `~/.claude/agents/<name>.md` — frontmatter `name` + `description` (+ `tools` to
   restrict, which is how you enforce "no messaging tools"), and the agent's prompt body
   from `agents/<name>/*.md`. `workspace: shared` ⇒ no new agent; fold into the main
   conversation instead.
4. **Schedules — expect to degrade every one.** There is no cron here. For `manual`,
   materialize the prompt as an invocable skill and tell the user the trigger in plain words
   ("ask me to run the weekly maintenance on Saturdays"). Record each degrade so `remove`
   and `verify` still enumerate it.
5. **Context blocks** inside the marker pair, appended to `~/.claude/CLAUDE.md` (or
   `AGENTS.md` if that is what the user keeps). Blank line before, trailing newline after —
   an identity file ending mid-marker corrupts the next capability's append.
6. **Onboarding** last, through `capability-onboard`, so the interview's answers reach
   `MOD.md` before anything reads them.

Order matters for one reason worth stating: the diff gate. Claude Code shows every write for
approval, so batch related edits rather than dribbling them — a user approving fifteen
one-line edits stops reading by the fourth.


## Introspection guide

- **What is installed:** `aos-lock list` / `aos-lock show <id>` is the authority, as always.
  The harness side is `ls -la ~/.claude/skills/` — the symlink targets tell you which
  renders are ours at a glance, and a *regular directory* where a symlink belongs is the
  drift `verify` cares about most.
- **What is loaded right now:** `/context` in-session. A skill that exists on disk but is
  absent there is a name or frontmatter problem — check that the folder name equals
  frontmatter `name`.
- **Available skills:** the skill registry is built from `~/.claude/skills/`,
  `<project>/.claude/skills/`, and installed plugins. Plugin skills appear namespaced
  (`plugin:skill`), which is why an aos installed name must still be globally unique
  (`reference/naming.md`) — the flat namespace is shared with them.
- **Agents:** `ls ~/.claude/agents/`. There is no verb that lists them in-session.
- **Settings actually in effect:** `~/.claude/settings.json` merged with
  `settings.local.json` merged with project settings; the local file wins. Read all three
  before concluding a key is unset.


## Secrets

**There is no secret store.** The options are the process environment or an `env` block in
`settings.json` — and `settings.json` is a plain file the user may well commit if it is the
project-scoped one.

Consequences, and they are hard limits rather than preferences:

- Never write a secret value into `settings.json`, `CLAUDE.md`, a skill, or `personal/`
  (which may be pushed to a private remote). The contract's rule holds: values go to the
  store, references go to files — and here "the store" means the user's own environment.
- A capability that requires a secret is installed by telling the user to export it
  (`export FOO_TOKEN=…` in their shell profile), then referencing `$FOO_TOKEN` by name.
- If a capability cannot work without a managed secret store, say so and stop rather than
  inventing a location. That is a `skip` in the install summary, not a workaround.


## Removal

Walk `aos-lock show <id>` backwards; nothing here is inferred from the filesystem.

1. Delete the symlinks under `~/.claude/skills/` that the lockfile records — the links only,
   never the render they point at, until step 3.
2. Delete `~/.claude/agents/<name>.md` for each agent the capability created. Leave agents
   it merely referenced.
3. Remove context blocks by their marker pair, leaving surrounding text untouched.
4. Uninstall the tool if the capability installed one: `uv tool uninstall <package>`.
5. Drop the pinned render under `<home>/personal/capabilities/<id>/` and the lockfile entry
   (`aos-lock remove <id>`).
6. Nothing to unschedule — there were no schedules to make (Rule zero).

Then confirm: `ls ~/.claude/skills/ | grep <prefix>` returns nothing, and `/context` in a
fresh session no longer lists them.


## Feature notes

- **`used_by` scoping is advisory here, not enforced.** Claude Code's subagents have no
  per-agent skills list, so a skill in `~/.claude/skills/` is reachable by the main
  conversation and, in practice, by subagents too. A capability that depends on scoping for
  *safety* (an agent that must not reach a skill) cannot get that guarantee on this harness —
  say so in the install summary rather than implying the scoping held.
- **Plan mode is native and worth using.** `capability-build`'s read-only gate is enforced
  by the harness here, not by prose — the strongest form of that gate across all sheets.
- **The diff gate is native too.** Every write is shown for approval, so the contract's
  STAGE→GATE→EXECUTE maps onto the harness's own behaviour instead of being simulated.
- **Two scopes, one namespace.** A user-scope skill and a project-scope skill with the same
  name collide; the collision gate must check both (`~/.claude/skills/` and every
  `<project>/.claude/skills/` the user cares about) plus installed plugins.
- **Skills are symlink-friendly**, which the install depends on: the folder is read through
  the link, and `reference/` files travel with it because the whole render directory is
  linked as one unit.
- **No `.aos/` convention of its own.** Machine state stays where the contract puts it
  (`<home>/.aos/`), not under `~/.claude/`.
