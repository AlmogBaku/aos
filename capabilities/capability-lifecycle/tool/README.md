# aos-lock

Deterministic lifecycle bookkeeping (ARCHITECTURE §2.4 capability tool): CAPABILITY.md
parse/validate and the lockfile. **The lockfile is this tool's file — agents call verbs,
never read or write the YAML directly.**

```
uv tool install --from <home>/upstream/capabilities/capability-lifecycle/tool aos-lock
# removal:  uv tool uninstall aos-lock
# zero-install one-off:
uvx --from <home>/upstream/capabilities/capability-lifecycle/tool aos-lock --help
```

Verbs: `manifest <dir>` · `skills <dir> [--check] [--harness-skills DIR]× [--json]` ·
`render <dir> <skill-id> --out DIR [--force]` · `init` ·
`record <cap> --version … --source-root upstream|personal|<org> --artifact …× --link …× --job …× --config-key …× --env-line …× --script …×` ·
`rehash <cap>` (refresh recorded hashes in place) · `verify [<cap>]` · `show <cap>` ·
`list` · `remove <cap>`. Household discovery: `--home` > `$AOS_HOME` > cwd-upward search
for `.aos/`. Exit codes: 0 ok · 1 generic (init over an existing lockfile) · 12 manifest
invalid · 13 drift · 14 no such entry · 15 no home · 16 artifact missing / not a symlink ·
17 skill-name collision.

## Skill names (§2.5)

`skills` prints each declared skill's **installed name** — the identity it ships under, and
the only name a harness ever sees. It is computed, never authored:

```
prefix           = skill_prefix if declared and non-empty, else "<capability-id>-"
installed name   = the id itself, if the id is the capability id (the entry skill)
                   the id itself, if it already starts with the prefix (never doubled)
                   prefix + id, otherwise
```

`--check` is the install gate. It fails with **17** if any installed name is already
claimed, looking in three places: every capability under `<home>/upstream` and
`<home>/personal`, the skill links the lockfile records for *other* capabilities, and each
`--harness-skills DIR` (a skills directory the harness itself reads — both `<name>/` dirs
and flat `<name>.md` files). Links this capability already owns are exempt, so re-installing
and upgrading are clean. A collision is resolved upstream by renaming the skill — never by
renaming at install time.

The first two sources need a household. It resolves from `--home`, `$AOS_HOME`, or by walking
up from the capability directory (which is inside one) — but **read the `checked:` lines the
clean report prints**: a source it could not reach is named in capitals. "Clean" against two
of three sources is not clean, so pass `--home` and the harness's skills dirs explicitly.

`render` is the mechanical half of materialization: it copies `skills/<id>/` whole (with
`reference/`, `templates/`, `scripts/`) to `<out>/<installed-name>/`, rewrites the render's
frontmatter `name` to the installed name, and stamps `metadata.aos.origin: <cap>@<version>`. It
leaves `{{mod: …}}` slots alone — filling those is the agent's job, afterwards. Re-running
with `--force` is byte-identical; without it, a non-empty destination is an error.

Lockfile entry fields (written only by `record`): `version`, `source_root` (which
household root shipped the capability), `artifacts` (path → sha256 — the pinned-render
files and native artifacts), `links` (harness symlink path → target, read from the link
itself; `verify` flags MISSING/RELINKED/DANGLING links), `schedules_owned` (job ids),
`config_keys`, `env_lines` (variable *names*, never values), `scripts`. Tests:
`uv run tests/tool/test_lock.py` (black-box subprocess; stdout + exit codes are the
contract).
