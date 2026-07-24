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

Verbs: `manifest <dir>` · `init` · `record <cap> --version … --source-root upstream|personal|<org> --artifact …× --link …× --job …× --config-key …× --env-line …× --script …×` ·
`rehash <cap>` (refresh recorded hashes in place) · `verify [<cap>]` · `show <cap>` ·
`list` · `remove <cap>`. Household discovery: `--home` > `$AOS_HOME` > cwd-upward search
for `.aos/`. Exit codes: 0 ok · 1 generic (init over an existing lockfile) · 12 manifest
invalid · 13 drift · 14 no such entry · 15 no home · 16 artifact missing / not a symlink.

Lockfile entry fields (written only by `record`): `version`, `source_root` (which
household root shipped the capability), `artifacts` (path → sha256 — the pinned-render
files and native artifacts), `links` (harness symlink path → target, read from the link
itself; `verify` flags MISSING/RELINKED/DANGLING links), `schedules_owned` (job ids),
`config_keys`, `env_lines` (variable *names*, never values), `scripts`. Tests:
`uv run tests/tool/test_lock.py` (black-box subprocess; stdout + exit codes are the
contract).
