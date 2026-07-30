# aos-kb — the kb capability's tool

Capability-shipped deterministic executor (ARCHITECTURE §2.4; RFC-004's outcome).
Installed at capability-install time:

    uv tool install --from <home>/upstream/capabilities/kb/tool aos-kb

…which puts the `kb` command on PATH (recorded in the lockfile; removal =
`uv tool uninstall aos-kb`). Zero-install alternative for one-off use:

    uvx --from <home>/upstream/capabilities/kb/tool kb --help

## What it refuses to do

Judgment-free by contract: never calls an LLM, never invokes an agent; files and exit
codes are the interface. `kb lint` is report-only by default — the report is for an
LLM to judge, not a verdict the tool hands down (`--ci` is the falsifiable exception,
for a hook or unattended runner that needs an exit code). No LLM-routed write may ever
reach an `audience: shared` base (§4.5 layer 2) — that's enforced by routing *method*,
never by refusing the verb.

## Verbs

Scaffold and register: `init` · `adopt` · `migrate` (layout 1 → 2, history intact)

The queue — `.kb/pending/`, one file per item, everything not yet an artifact of its
own: `pending` (add/list/resolve) · `ingest` (pending capture → `_raw/`) · `refuse` ·
`verify`

Write: `capture` · `set` (mutate frontmatter) · `prune` (delete what `expires:` says
is over) · `archive` (git rm + a reason) · `config` (get/set) · `commit` (attribute a
hand-write)

Fetch — `--where`/`--without` on all of them: `find` · `inbox` · `state` · `search` ·
`links`

Everything else: `lint` · `grants` · `index` · `sync` · `history` · `import survey`

## Layout

`layout: 2` (`.kb/base.yml`). `.kb/` is the tool's own — `pending/` waiting on
someone, `work/` in progress, `cache/` rebuildable and gitignored. `_raw/` is flat and
immutable once ingested; `entities/ concepts/ projects/ profile/` are wiki zones,
current-truth only. `expires:` is the only lifetime rule the tool knows.

See the `kb` entry skill and `design/kb-methodology.md` §9.
