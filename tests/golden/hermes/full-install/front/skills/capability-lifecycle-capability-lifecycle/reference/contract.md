# The install contract

Binds every lifecycle operation, on every harness, with or without a cheat-sheet.

- **The household is the ground truth of where things live** (§3.1): `<home>` (default
  `~/aos`) contains `upstream/` (the kit clone — pristine, never anything personal, not
  even untracked files), `personal/` (the user's one private git repo: MOD ledgers at
  mirrored capability paths, the pinned renders, their private capabilities), and
  `.aos/` (machine state — the lockfile). A capability id resolves against `personal/`
  first, then `upstream/`; a personal package shadowing an upstream id is reported
  loudly at install/upgrade, never silently preferred.
- **The diff gate is never optional.** Nothing lands in the harness until the user has
  seen the full diff of what you are about to write and approved it (§5.4). The three
  phases are explicit: **STAGE** (render the personalized artifacts into `personal/`'s
  working tree and compute the exact native command plan — commit nothing, touch no
  harness file), **GATE** (show contents + plan; for re-renders the gate *is*
  `git -C <home>/personal diff`), **EXECUTE** (commit the render in `personal/` with a
  dated message, create the links, run the native plan). Nothing touches the harness
  before the gate. Where the harness has a native plan/read-only mode (cheat-sheet
  Primitive mapping, `plan mode` row), STAGE runs inside it and the GATE approval is
  the exit.
- **You never write** any `MOD.md` except through `capability-evolver` or an interview,
  and you never edit shipped capability files in any source root — personalization
  lives only in `personal/` (the ledgers and the pinned renders).
- **You never contribute without approval.** You never open a PR, file an issue,
  comment, +1, or push to upstream — or any repo the user doesn't own — without the
  user's explicit approval or request. No exceptions. Offers are cheap; writes that
  leave the machine are the user's alone to authorize.
- **The lockfile is `aos-lock`'s file.** Everything you materialize is recorded — one
  entry per capability+harness: version, source root, render-file paths + sha256,
  harness symlinks (`--link` — the tool reads each link's target itself), job ids under
  `schedules_owned`, config keys, `.env` variable names, scripts; a capability's
  installed tool binary is recorded as an `--artifact` (hash the command on PATH). You
  call verbs (`aos-lock --help`), you never read or write the YAML. No lockfile record,
  no artifact. If a crash lands between EXECUTE and `record`, everything written
  carries provenance anyway — re-introspect for the tags and record or remove what you
  find.
- **Skills materialize as pinned renders + symlinks, never copies.** Render each
  declared skill whole (`reference/`, `scripts/`, `templates/` travel; scripts are
  executed, never loaded as context) into
  `personal/capabilities/<capability>/skills/<id>/`, filling `{{mod: …}}` slots (leave
  unfilled slots intact) and adding an `x-aos-origin: <capability>@<version>` line
  **inside** the render's YAML frontmatter block (between the `---` delimiters, beside
  `name:`). Then symlink it into the skills location of every agent in its `used_by` as
  **`<capability>-<id>`** — the frontmatter `name` stays as shipped unless the
  cheat-sheet says the harness needs it to match the folder. Container harnesses
  resolve links only if `<home>/personal` is mounted read-only — the cheat-sheet's
  Materialization guide says how; without the mount, stop and say so (never fall back
  to copying: one canonical render, everywhere).
- **The persist hook**: after every ledger write (interview, evolve, retirement,
  drift-fold) and every render, commit `personal/` with a dated one-line message —
  you, not the user; silently. The `personal/` git history is the primary safety net;
  rollback is `git revert`.
- **Schedules** are named `aos:<capability>:<schedule-id>` and single-owner (§5.5): check
  across agents first — exists elsewhere → ask the user to reassign, never duplicate.
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
  markers; never touch text outside them.
- **Secrets**: values go to the harness's store, never into files or chat — and never
  into `personal/` (it may be pushed to a private remote); `MOD.md` and configs carry
  references only — `{store: <name>, key: <key>}`.
- **Removal** walks the lockfile entry backwards; `MOD.md` is never deleted (§3.3), and
  render deletions in `personal/` happen via a commit (revertible). Verify by
  re-running introspection until no aos provenance (`x-aos-origin:`, `aos:` names,
  marker blocks, links into `personal/`) remains.
- **References resolve by three rules.** Inside a skill's own folder: relative paths
  (the whole-folder render keeps them valid — and links preserve them). Across skills:
  by skill *name* — never a parent-directory path (link names differ from shipped dirs;
  lint bans the pattern). Into the household (capability sources, cheat-sheets, MOD
  ledgers): shipped files write a `<home>/…` placeholder; the transform bakes the real
  household path into renders (same pass as `{{mod}}`), and scheduled commands get
  `--home`/`AOS_HOME` baked the same way. The lifecycle capability's own skills are
  render-stable (no `{{mod}}` slots) and keep the placeholder — resolve it at use time
  via `aos-lock`'s household discovery.
- Harness-owned files (e.g. Hermes `config.yaml`, `cron/jobs.json`) are touched only
  through the harness's own CLI, per the cheat-sheet.
