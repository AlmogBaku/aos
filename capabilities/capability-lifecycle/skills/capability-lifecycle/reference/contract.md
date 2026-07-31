# The install contract

## Contents

- The household, and where everything lives
- The diff gate · MOD.md authorship · contribution approval
- The lockfile, and what gets recorded
- Installed skill names, renders, and symlinks
- The persist hook · schedules · context blocks · secrets
- Removal, and how references resolve

Binds every lifecycle operation, on every harness, with or without a cheat-sheet.

## The household, and where everything lives

- **The household is the ground truth of where things live** (§3.1): `<home>` (default
  `~/aos`) contains `upstream/` (the kit clone — pristine, never anything personal, not
  even untracked files), `personal/` (the user's one private git repo: MOD files at
  mirrored capability paths, the pinned renders, their private capabilities), `.aos/`
  (machine state — the lockfile, plus any machine-local file a capability's tool writes for
  itself: kb's `kb-principal.yml` is the one today. Machine-local means gitignored and
  per-machine, so it is recreated by the tool rather than carried between machines), and
  `vendor/` (third-party skills aos references rather
  than ships — cloned, symlinked, and recorded like anything else, but never rendered and
  never origin-tagged: they are not ours to modify). A capability id resolves against `personal/`
  first, then `upstream/`; a personal package shadowing an upstream id is reported
  loudly at install/upgrade, never silently preferred. **A directory is only a package if it
  holds a `CAPABILITY.md`** — `personal/capabilities/<id>/` exists for every capability the
  user has answers for (it is the mirrored overlay path), so treating a MOD-only directory
  as a second source would report a shadow on every ordinary install.

## The diff gate · MOD.md authorship · contribution approval

- **The diff gate is never optional.** Nothing lands in the harness until the user has
  seen the full diff of what you are about to write and approved it (§5.4). The three
  phases are explicit: **STAGE** (render the personalized artifacts into `personal/`'s
  working tree and compute the exact native command plan — commit nothing, touch no
  harness file), **GATE** (show contents + plan; for re-renders the gate *is* a git diff in
  `personal/` — **stage first, scoped to the capability, so added files are visible**:
  `git -C <home>/personal add -A -- capabilities/<id>` then
  `git -C <home>/personal diff --staged -- capabilities/<id>`. A bare `git diff` hides
  untracked files, and a re-render that *adds* a skill or a `reference/` page is the
  commonest upgrade shape), **EXECUTE** (commit the staged render with a dated message,
  create the links, run the native plan). Declined → restore that capability only,
  additions included: `git -C <home>/personal restore --staged --worktree --
  capabilities/<id>`, then `git -C <home>/personal clean -fd -- capabilities/<id>` as
  belt-and-braces (`restore` already removes the staged additions and prunes the
  directories they created; `clean` catches anything staging missed). **Every one of
  these commands is path-scoped** — a bare `add -A` or `reset --hard` would swallow or
  destroy unrelated work elsewhere in `personal/`, including untracked files. One
  caveat to state out loud before staging: `add -A -- capabilities/<id>` also picks up
  any *pre-existing untracked* file the user keeps inside that capability's directory,
  and declining would delete it — check `git status -- capabilities/<id>` first and say
  what you found. Nothing touches the harness
  before the gate. Where the harness has a native plan/read-only mode (cheat-sheet
  Primitive mapping, `plan mode` row), STAGE runs inside it and the GATE approval is
  the exit.
- **You never write** any `MOD.md` except through `capability-evolve` or an interview,
  and you never edit shipped capability files in any source root — personalization
  lives only in `personal/` (the MOD files and the pinned renders).
- **You never contribute without approval.** You never open a PR, file an issue,
  comment, +1, push, fork, or create a branch on a remote — for upstream or any repo
  the user doesn't own — without the user's explicit approval or request. No exceptions. Offers are cheap; writes that
  leave the machine are the user's alone to authorize.

## The lockfile, and what gets recorded

- **The lockfile is `aos-cap`'s file.** Everything you materialize is recorded — **one
  entry per capability, covering every harness it is installed into** (`record` replaces
  the entry wholesale, so a second-harness install must re-record the *combined* set:
  start from `aos-cap show <id>` and add to it, never call `record` with a partial
  list). An entry carries: version, source root, render-file paths + sha256,
  harness symlinks (`--link` — the tool reads each link's target itself), job ids under
  `schedules_owned`, config keys, `.env` variable names, scripts; a capability's
  installed tool binary is recorded as an `--artifact` — but **resolve the symlink first**
  (`readlink -f $(command -v <tool>)`): `uv tool install` puts a *link* on PATH, and a symlink
  passed as `--artifact` is refused at exit 16 by design (that flag hashes files; links are
  `--link`'s job). Recording the resolved binary is what lets `verify` notice a stale tool. You
  call verbs (`aos-cap --help`), you never read or write the YAML. No lockfile record,
  no artifact. If a crash lands between EXECUTE and `record`, everything written
  carries provenance anyway — re-introspect for the tags and record or remove what you
  find.

## Installed skill names, renders, and symlinks

- **A skill's installed name is computed, and it is single-owner.** `aos-cap skills <cap-dir>`
  gives you the name each skill ships under (`<skill_prefix><id>`; the entry skill keeps the
  capability id). **Gate before you materialize**:
  `aos-cap --home <home> skills <cap-dir> --check --harness-skills <each skills dir this
  harness reads>`
  — exit 17 means the name is already claimed by another capability in the household, by a
  lockfile-recorded link, or by a skill the harness already has (aos-installed or not).
  Stop and report it; **never rename at install time** — the name belongs to the package, so
  the fix is upstream (`capability-contribute`) or in the user's own package. Full rules:
  the naming rules the `capability-lifecycle` entry skill links.
- **An agent's name is computed and single-owner too.** Harnesses keep a flat agent namespace
  as well, so `aos-cap --home <home> agents <cap-dir> --check` gates any capability that
  ships `agents/` — same `<skill_prefix><agent-id>` computation, same exit 17, same
  never-rename-here rule. It reads two of three sources and names the third (agents already
  in the harness — no enumeration yet) in capitals.
- **Skills materialize as pinned renders + symlinks, never copies.** `aos-cap render
  <cap-dir> <id> --out personal/capabilities/<capability>/skills` does the mechanical half:
  the whole folder travels (`reference/`, `scripts/`, `templates/` — scripts are executed,
  never loaded as context), the render lands under the **installed name**, its frontmatter
  `name` is rewritten to match, and `metadata.aos.origin: <capability>@<version>` is stamped inside
  the frontmatter block. Then you fill `{{mod: …}}` slots in the render (leave unfilled slots
  intact) — that judgment is yours, the copy is not. Symlink the render into the skills
  location of every agent in its `used_by`, under the same installed name: **dir, frontmatter
  `name`, and link all agree, on every harness — no per-harness renaming.** Container
  harnesses resolve links only if `<home>/personal` is mounted read-only — the cheat-sheet's
  Materialization guide says how; without the mount, stop and say so (never fall back to
  copying: one canonical render, everywhere).

- **A `depends.host` feature is a *harness capability*, answered by the cheat-sheet's
  Feature notes table — never by probing the user's live configuration.** ✓ means this
  harness can express the feature; a platform the user has not paired yet is a setup note
  for them, not an install stop. Stop on `required` only when the table says the harness
  cannot do it at all (or there is no sheet and your own reading of the harness says so).
  Getting this backwards fails an install that would have worked, which is worse than the
  degraded-mode path the vocabulary exists to enable.

## The persist hook · schedules · context blocks · secrets

- **The persist hook**: after every MOD write (interview, evolve, retirement,
  drift-fold) and every render, commit `personal/` with a dated one-line message —
  you, not the user; silently. The `personal/` git history is the primary safety net;
  rollback is `git revert`.
- **Schedules** are named `aos:<capability>:<schedule-id>` and single-owner (§5.5): check
  across agents first — exists elsewhere → ask the user to reassign, never duplicate.
  **An exec-type entry names no agent, so it is hosted by the agent that owns the
  capability's other schedules** — the archiver for kb's `sync`, for instance — and by the
  front agent when the capability declares no agent at all. Nothing runs it but the
  scheduler, so placement is a bookkeeping choice, and keeping a capability's jobs in one
  place is what makes the removal walk and the single-owner check enumerable.
  Exec-type entries run the tool the capability's briefing installs (verify
  `uv --version` before wiring); a path-form `exec:` runs as
  `uv run <home>/upstream/<path-and-args>` (personal capabilities:
  `<home>/personal/<path-and-args>`). An absent host feature triggers the schedule's
  declared degraded mode: `manual` = materialize the prompt as an invocable skill and
  tell the user how to run it · `inline` = append it (inside markers) to an existing
  aos-owned job · `skip` = skip it, say so in the install summary, and record it in
  your report — the deferred `doctor` verb (RFC-004) will make skips queryable.
- **Context blocks** are appended only inside
  `<!-- aos:<capability>@<version> begin -->` … `<!-- aos:<capability>@<version> end -->`
  markers; never touch text outside them. A capability that owns more than one block
  discriminates them the way schedules do — `aos:<capability>:<block-id>@<version>` — so each
  is independently replaceable on upgrade. Leave a blank line before a block and a trailing
  newline after it: an identity file that ends mid-marker makes the next capability's append
  start on the `end -->` line, which corrupts both blocks.
- **Secrets**: values go to the harness's store, never into files or chat — and never
  into `personal/` (it may be pushed to a private remote); `MOD.md` and configs carry
  references only — `{store: <name>, key: <key>}`.

## Removal, and how references resolve

- **Removal** walks the lockfile entry backwards; `MOD.md` is never deleted (§3.3), and
  render deletions in `personal/` happen via a commit (revertible). Verify by
  re-running introspection until no aos provenance (`metadata.aos.origin`, `aos:` names,
  marker blocks, links into `personal/`) remains.
- **References resolve by three rules.** Inside a skill's own folder: relative paths
  (the whole-folder render keeps them valid — and links preserve them), and never into a
  sibling `reference/` file — depth is one level from SKILL.md. Across skills: by the
  skill's **installed** name — never a parent-directory path (a source id is
  capability-local and names nothing once installed; lint bans both patterns). Into the
  household (capability sources, cheat-sheets, MOD
  files): shipped files write a `<home>/…` placeholder; the transform bakes the real
  household path into renders (same pass as `{{mod}}`), and scheduled commands get
  `--home`/`AOS_HOME` baked the same way. The lifecycle capability's own skills are
  render-stable (no `{{mod}}` slots) and keep the placeholder — resolve it at use time
  with `aos-cap --home <path> home` (or bare `aos-cap home` from inside the
  household; exit 15 when there is none), never by guessing `~/aos`.
- Harness-owned files (e.g. Hermes `config.yaml`, `cron/jobs.json`) are touched only
  through the harness's own CLI, per the cheat-sheet.
