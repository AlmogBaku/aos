# aos-cap

Deterministic lifecycle bookkeeping (ARCHITECTURE §2.4 capability tool): CAPABILITY.md
parse/validate and the lockfile. **The lockfile is this tool's file — agents call verbs,
never read or write the YAML directly.**

```
uv tool install --from <aos_home>/upstream/capabilities/capability-lifecycle/tool aos-cap
# removal:  uv tool uninstall aos-cap
# zero-install one-off:
uvx --from <aos_home>/upstream/capabilities/capability-lifecycle/tool aos-cap --help
```

Verbs: `manifest <dir>` · `skills <dir> [--check] [--harness-skills DIR]× [--json]` ·
`agents <dir> [--check] [--json]` ·
`render <dir> <skill-id> --out DIR [--force]` · `init` ·
`record <cap> --version … --source-root upstream|personal|<org> --artifact …× --link …× --uses-link …× --job …× --config-key …× --env-line …× --script …×` ·
`rehash <cap>` (refresh recorded hashes in place) · `verify [<cap>]` · `show <cap>` ·
`list` · `remove <cap>` · `harness set <runtime> [--source PATH] [--sheet PATH]` · `harness show` ·
`swap <cap>` · `discard <cap>` · `migrate rendered [--apply|--finish] [--scan DIR]× [--ignore GLOB]×`. Household discovery: `--home` > `$AOS_HOME` > `~/aos`. Exit codes: 0 ok · 1 generic (init over an existing lockfile) · 12 manifest
invalid · 13 drift · 14 no such entry · 15 no home · 16 artifact missing / not a symlink ·
17 skill- or agent-name collision · 18 unresolvable `{{skill:}}`/`{{agent:}}` slot ·
19 a link another entry already records · 20 no harness recorded · 21 not a capability id,
or a symlinked render directory · 22 nothing staged · 23 the staged render bakes its own
staging path or drops a linked target · 24 a path the layout forbids there · 25 migrate
refused · 26 an interrupted swap was put back.

## The rendered tree — `swap`, `discard`, `migrate rendered`

Every render lives at `<aos_home>/rendered/<id>/`: unversioned, machine-local build output,
and every harness link points into it. Inside the household, `render` writes only under
`rendered/.staging/` (exit **24** otherwise, checked on the resolved path; an `--out` outside
the household stays allowed). `record` and `rehash` refuse a staged path (**24**).

- `swap <id>` puts the staged render live. The live one is renamed to
  `rendered/.replaced/<id>`, the staged one renamed in, and the replaced one sent to the OS
  trash (`send2trash`), so a link into `rendered/<id>` never points at nothing for longer than
  one rename. It refuses, without moving anything:
  - an id outside the kit's name grammar, or a symlinked directory (**21**);
  - nothing staged (**22**);
  - a staged file that names its own `.staging/<id>` path, or a staged tree missing a
    recorded link target (**23**).

  A `.replaced/<id>` left by a crash is trashed when a live render exists, and put back live
  (**26**) when none does.
- `discard <id>` sends the staged render to the trash; the live one is untouched.
- `migrate rendered` moves a pre-0.7.0 household's renders out of `personal/` in three
  steps, the old paths resolving until the last:
  - the plan writes nothing but its scan set, `.aos/migrate-rendered.yaml`;
  - `--apply` copies (no bytecode; old paths rewritten in UTF-8 text only), re-points every
    link, and rewrites the lockfile and `harness.yml`, recording every moved file;
  - `--finish` refuses (**25**) while any outside reference or link still names an old
    render, then trashes them.

  `--apply` refuses (**25**) while a render has drift or uncommitted changes. References
  are printed as `path:line` only: the scan reads harness homes, which hold keys.

## The harness record

`harness set <runtime>` writes `<aos_home>/.aos/harness.yml` — `{harness, sheet, cli}` — once per
household (machine-local, written only through this tool); `harness show` exits **20** when nothing
is recorded. `render` ships every cheat-sheet: one household can serve several harnesses.
`aos-session` reads the record: `sheet` is where `mapping.session` lives, and `cli` is the absolute path
of the harness launcher, resolved here from the first word of the kit sheet's `mapping.session.open`,
so a caller with a reduced PATH still reaches the harness. Run `harness set` again if it moves.

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
claimed, looking in three places: every capability under `<aos_home>/upstream` and
`<aos_home>/personal`, the skill links the lockfile records for *other* capabilities, and each
`--harness-skills DIR` (a skills directory the harness itself reads — both `<name>/` dirs
and flat `<name>.md` files). Links this capability already owns are exempt, so re-installing
and upgrading are clean. A collision is resolved upstream by renaming the skill — never by
renaming at install time.

The first two sources need a household. It resolves from `--home`, `$AOS_HOME`, else `~/aos`
— but **read the `checked:` lines the clean report prints**: a source it could not reach is
named in capitals. "Clean" against two of three sources is not clean, so pass `--home` and
the harness's skills dirs explicitly.

## Agent names — the same identity, one directory over

Harnesses keep agents in a flat per-harness namespace too (`~/.hermes/profiles/<name>/`,
`~/.claude/agents/<name>.md`), so two capabilities shipping `archiver` silently override each
other. `agents <dir>` prints each `agents/*.agent.yaml`'s **installed name**, computed by the
identical three lines above from the capability's `skill_prefix` — `archiver` in `kb` ships as
`kb-archiver`. There is no `agent_prefix` field: §2.2's rule of two, and no in-repo capability
wants divergent prefixes.

`--check` is the same single-owner gate under the same exit **17** — one code for one hazard,
whichever namespace it lands in — with the same never-rename-at-install-time rule. It reads
**two** of the three sources: the household's other capabilities and the lockfile's recorded
links. Enumerating the agents *already in the harness* is deferred, because it is a different
command per harness (`hermes profile list`, `ls ~/.claude/agents/`, `openclaw agents list`,
`ncl groups list`, `ls agents/`) for a source no shipped capability collides on today — and the
report says `NO --harness-agents SUPPORTED YET` in as many words rather than letting a skipped
source read as an empty one. A capability with no `agents/` directory prints nothing and exits
0; that is the common case, not an error.

`render` is the mechanical half of materialization: it copies `skills/<id>/` whole (with
`reference/`, `templates/`, `scripts/`) to `<out>/<installed-name>/`, rewrites the render's
frontmatter `name` to the installed name, and stamps `metadata.aos.origin: <cap>@<version>`. It
leaves `{{mod: …}}` slots alone — filling those is the agent's job, afterwards. Re-running
with `--force` is byte-identical; without it, a non-empty destination is an error.

## Name slots — `{{skill:}}` and `{{agent:}}`

Installed names are computed, so shipped prose must never hardcode one: a `skill_prefix`
change would silently invalidate every reference. `render` substitutes, in every `*.md`
under the render:

| slot | becomes |
|---|---|
| `{{skill: <id>}}` | this capability's skill, at its installed name |
| `{{agent: <id>}}` | this capability's agent — same prefix; agents share one flat namespace with skills |
| `{{skill: <cap>/<id>}}` · `{{agent: <cap>/<id>}}` | another capability's, at *its* prefix |

A leading backslash makes the slot a literal example: `\{{skill: <id>}}` renders as
`{{skill: <id>}}`, neither substituted nor validated (the same escape works for
`{{mod:}}`) — needed because this capability documents the syntax it is itself rendered by.

A slot naming no declared skill/agent, an unresolvable capability, or one that exists in
**both** household roots is exit **18**: every error is printed and the render is removed,
so a half-substituted skill can never look complete to the next step. Cross-capability ids
resolve `personal/` first then `upstream/` — a shadowed id is reported, never preferred.
`{{mod: …}}` slots are untouched by all of this: the agentic transform owns them.

Lockfile entry fields (written only by `record`): `version`, `source_root` (which
household root shipped the capability), `artifacts` (path → sha256 — the render
files under `rendered/<id>/` and native artifacts), `links` (harness symlink path → target, read from the link
itself; `verify` flags MISSING/RELINKED/DANGLING links), `uses_links` (the same shape, for
another capability's skill this capability's `uses` linked into one of its agents — kept
apart because `links` basenames are name claims and these are not), `cron_owned` (job ids),
`config_keys`, `env_lines` (variable *names*, never values), `scripts`. One owner per
link: `record` refuses (19) a path another entry already records, own or used. Tests:
`uv run tests/tool/test_cap.py` (black-box subprocess; stdout + exit codes are the
contract).
