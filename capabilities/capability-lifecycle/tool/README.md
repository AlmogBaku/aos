# aos-lock

Deterministic lifecycle bookkeeping (ARCHITECTURE §2.4 capability tool): CAPABILITY.md
parse/validate and the lockfile. **The lockfile is this tool's file — agents call verbs,
never read or write the YAML directly.**

```
uv tool install --from <clone>/capabilities/capability-lifecycle/tool aos-lock
# removal:  uv tool uninstall aos-lock
# zero-install one-off:
uvx --from <clone>/capabilities/capability-lifecycle/tool aos-lock --help
```

Verbs: `manifest <dir>` · `init` · `record <cap> --version … --artifact …× --job …× --config-key …× --env-line …× --script …×` ·
`rehash <cap>` (refresh recorded hashes in place) · `verify [<cap>]` · `show <cap>` · `list` · `remove <cap>`. Clone discovery: `--clone` >
`$AOS_CLONE` > cwd-upward search for `.aos/`. Exit codes: 0 ok · 1 generic
(init over an existing lockfile) · 12 manifest invalid · 13 drift · 14 no such entry ·
15 no clone · 16 artifact missing.

Lockfile entry fields (written only by `record`): `version`, `artifacts` (path → sha256),
`schedules_owned` (job ids), `config_keys`, `env_lines` (variable *names*, never values),
`scripts`. Tests: `uv run tests/tool/test_lock.py` (black-box subprocess; stdout + exit
codes are the contract).
