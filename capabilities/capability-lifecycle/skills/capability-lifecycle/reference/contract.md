# The install contract

Binds every lifecycle operation, on every harness, with or without a cheat-sheet.

- **The diff gate is never optional.** Nothing lands in the harness until the user has
  seen the full diff of what you are about to write and approved it (§5.4). The three
  phases are explicit: **STAGE** (compute every artifact's content and the exact native
  command plan — touch nothing), **GATE** (show contents + plan), **EXECUTE** (run it).
  Nothing touches the harness before the gate.
- **You never write** any `MOD.md` except through `capability-evolver` or an interview,
  and you never edit shipped capability files in the clone — personalization lives only
  in the overlay (§3.1) and the materialized artifacts.
- **The lockfile is `aos-lock`'s file.** Everything you materialize is recorded — one
  entry per capability+harness: version, artifact paths + sha256, job ids under
  `schedules_owned`, config keys, `.env` variable names, scripts/hooks. You call verbs
  (`aos-lock --help`), you never read or write the YAML. No lockfile record, no
  artifact. If a crash lands between EXECUTE and `record`, everything written carries
  provenance anyway — re-introspect for the tags and record or remove what you find.
- **Skills** are copied **whole** (`reference/`, `scripts/`, `templates/` travel with the
  skill; scripts are executed, never loaded as context) into the skills location of every
  agent in their `used_by`, as **`<capability>-<id>/`** — the frontmatter `name` stays as
  shipped unless the cheat-sheet says the harness needs it to match the folder. Fill
  `{{mod: …}}` slots (leave unfilled slots intact) and add an
  `x-aos-origin: <capability>@<version>` line **inside** the materialized copy's YAML
  frontmatter block (between the `---` delimiters, beside `name:`).
- **Schedules** are named `aos:<capability>:<schedule-id>` and single-owner (§5.5): check
  across agents first — exists elsewhere → ask the user to reassign, never duplicate.
  Exec-type entries run the tool the capability's briefing installs; a path-form `exec:`
  runs as `uv run <clone>/<path-and-args>`. An absent host feature triggers the
  schedule's declared degraded mode: `manual` = materialize the prompt as an invocable
  skill and tell the user how to run it · `inline` = append it (inside markers) to an
  existing aos-owned job · `skip` = record it so it is reported.
- **Context blocks** are appended only inside
  `<!-- aos:<capability>@<version> begin -->` … `<!-- aos:<capability>@<version> end -->`
  markers; never touch text outside them.
- **Secrets**: values go to the harness's store, never into files or chat; `MOD.md` and
  configs carry references only — `{store: <name>, key: <key>}`.
- **Removal** walks the lockfile entry backwards; `MOD.md` is never deleted (§3.3).
  Verify by re-running introspection until no aos provenance (`x-aos-origin:`, `aos:`
  names, marker blocks) remains.
- **References resolve by three rules.** Inside a skill's own folder: relative paths
  (the whole-folder copy keeps them valid). Across skills: by skill *name* — never a
  parent-directory path (materialization renames dirs; lint bans the pattern). Into the
  clone (capability sources, cheat-sheets, MOD ledgers): shipped files write a
  `<clone>/…` placeholder; the transform bakes the real clone path into materialized
  copies (same pass as `{{mod}}`), and scheduled commands get `--clone`/`AOS_CLONE`
  baked the same way.
- Harness-owned files (e.g. Hermes `config.yaml`, `cron/jobs.json`) are touched only
  through the harness's own CLI, per the cheat-sheet.
