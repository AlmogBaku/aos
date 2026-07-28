# kb reference

Lookup, not narrative. The reasoning is in [design.md](design.md).

## Layout, file by file

| Path | Owner | What it is |
|---|---|---|
| `.kb/base.yml` | tool | machine config: layout, name, audience, purpose, types, zones, curation, state cap, frontmatter extensions |
| `.kb/state/<principal>.yml` | `agent:main` | the capped attention window, one shard per principal — always, so going shared needs no move |
| `.kb/pending/<ts>-<slug>.md` | tool | one file per pending item; `kind:` and `waits_on:` in frontmatter |
| `.kb/work/<src>/` | the running procedure | long-lived coordination files (import agreement, progress checklist) |
| `.kb/cache/` | tool | gitignored, rebuildable — search index, link graph |
| `AGENTS.md` | user | the contract, and the Grants table. **Must stay at root**: it is the filename harnesses auto-load for a working directory |
| `README.md` | user (seeded by `kb init` from the template's `base.README.md`) | the base explained to a human — the front door, since `AGENTS.md` addresses agents and `index.md` maps content |
| `index.md` | `agent:archiver` | the map — one line per page, from each page's `description:` |
| `_raw/` | `agent:archiver` | source material, flat, immutable once ingested, never expires |
| `entities/ concepts/ projects/ profile/` | `agent:archiver` (`profile/` is `agent:main`) | wiki pages, current truth only |
| `.gitattributes` | tool | git-LFS patterns for large binaries |
| `<home>/.aos/kb-principal.yml` | tool | machine-local, gitignored: the principal list |
| `<home>/personal/kb-registry.yaml` | user | the registry of every base — overlay family, never shipped upstream |

## Page frontmatter

**Universal** — every wiki page:

| Field | Type | Notes |
|---|---|---|
| `title` | string | |
| `description` | string | one line; feeds `index.md` |
| `type` | enum | must be in `.kb/base.yml` `types` (closed set) |
| `created` | date | |
| `timestamp` | date | last meaningful change; bump on content edits only |
| `tags` | list | |
| `aliases` | list | variant spellings — cheaper than duplicate pages |
| `verified` | bool | agent-written pages start `false`; `kb verify` flips it |
| `origin` | path | the capture this page came from |
| `expires` | date | optional; the only lifetime field kb interprets |
| `review_by` | date | optional; *ask me again* — **not** a deletion date |
| `meta` | map | free per-doc fields; used by 2+ docs → graduate to `frontmatter.extensions` |

**Raw captures** additionally: `source`, `source_sha256`, `captured_at`, `captured_by`,
`kb_routing` (when routed), `failed` (when the capture errored), `corrects` (when written
with `--corrects`).

Identity is the file path. There is no slug field, and filenames are
lowercase-hyphen-ASCII and never change.

## `.kb/pending/` vocabulary

`kind:` — exactly five:

| kind | Written when |
|---|---|
| `kind: capture` | `kb capture` files something for later ingest |
| `kind: refusal` | a write was denied by the grants table; the payload stayed with the caller |
| `kind: conflict` | `kb sync` hit a genuine divergence it will not auto-resolve |
| `kind: entity` | an unresolved `@mention` — never auto-stubbed into a page |
| `kind: finding` | a lint critical, an eviction proposal, or an agent's judgment call |

`waits_on:` — exactly two: `agent` (an agent will process it) · `human` (nobody but a person
can move it).

## The verbs

| Verb | Reads / Writes | What it does |
|---|---|---|
| `kb init` | W | scaffold a new base, register it, write the principal file |
| `kb adopt` | W (registry only) | register an existing tree; zero writes into it |
| `kb migrate` | W | previous layout → current, with `git mv` so history follows |
| `kb capture` | W | file content into `.kb/pending/`; `--corrects <path>` links a correction |
| `kb ingest` | W | move a pending capture into `_raw/` |
| `kb pending add\|list\|resolve` | R/W | the queue |
| `kb inbox` | R | a view: this principal's pending items (`--all` for everyone's, curator only) |
| `kb set <page> k=v …` | W | generic frontmatter mutation, one commit |
| `kb prune` | W | delete what has expired, report what went |
| `kb archive <page> --reason` | W | `git rm` plus an attributed commit |
| `kb find` | R | metadata query over frontmatter |
| `kb search` | R | BM25 full text; exact and alias hits flagged `EXISTS` |
| `kb links <page>` | R | backlinks, neighbours, orphans |
| `kb state add\|bump\|drop\|check\|show` | R/W | the attention window |
| `kb grants check` | R | GRANTED/DENIED plus an exit code |
| `kb lint` | R | the deterministic catalog — stdout **is** the report |
| `kb index rebuild` | W | regenerate `index.md` |
| `kb sync [--all]` | W | fast-forward, merge only on genuine divergence |
| `kb commit --verb …` | W | attribute a hand-edit |
| `kb history` | R | recent activity, from git |
| `kb refuse` | W | record a denied write as a `kind: refusal` entry |
| `kb verify <page>` | W | flip `verified: true` |
| `kb import survey <src>` | R | inventory and shape detection of a foreign tree |
| `kb config get\|set` | R/W | `principal.*` is machine-local; everything else base-local |

Every write verb makes its own commit: author = the human principal, committer = the acting
agent, with the verb and path in `aos-verb` / `aos-path` trailers.

## The query language

Applies to **every** fetch verb, not just one.

| Form | Meaning |
|---|---|
| `--where key=value` | equality; repeatable; dotted paths (`kb_routing.status`) |
| `--without key` | the field is absent — "committed but unscheduled" is `--without block` |
| `--where key<value` | also `<=` `>` `>=` `=` |
| relative dates | `today`, `today+7d`, `today-2w` — computed in the tool, never by a model |

Example: `kb find --where type=action --where status=next --where due<today+3d --without block`

## The grants table

The first markdown table under `## Grants` in `AGENTS.md`. Columns are parsed — do not
rename them.

| Column | Values |
|---|---|
| `subject` | a principal id · `user` · `agent:<name>` · `capability:<id>` · `*` (any *registered* subject) |
| `object` | space-separated git-style globs relative to the base root (`**` crosses `/`, `*` does not) |
| `verbs` | a subset of `read write route-into grant` |
| `grantor` | who granted it — `user` for everything except the root row |
| `granted` | ISO date |
| `via` | `<capability>@<version>` for install-time rows, so removal is mechanical |
| `notes` | free text |

Default posture is **deny**: no row, no verb, `read` included. An unregistered subject
matches nothing, not even `*`. `grant` is user-only.

## Exit codes

Two ranges, deliberately: single digits are answers and outcomes, the teens mean "this tree
is not one I can speak to".

| Code | Reachable from | Meaning |
|---|---|---|
| 0 | any verb | success |
| 1 | any verb | the default refusal — `kb: error: …` on stderr, nothing written. Also `grants check` answering DENIED, `lint --ci` with criticals, and `commit` with nothing to commit |
| 2 | any verb · `sync` | **two meanings.** From the CLI framework: a usage error — unknown verb, missing required option, value outside a closed set. From `sync`: the local commit failed, so nothing was pushed |
| 3 | `sync` only | a genuine divergence. The merge was aborted clean and recorded as a `kind: conflict` entry in `.kb/pending/`; a human resolves it |
| 4 | `sync` only | the local side committed but the push never landed after retries |
| 5 | `sync` only | a git operation was left mid-flight (rebase, merge, cherry-pick, revert). Nothing was staged — sync refuses rather than committing conflict markers |
| 10 | any verb · `migrate` | not a base: no `.kb/base.yml`. Adopt it, or check `--base` |
| 11 | any verb | layout mismatch — a tree on the previous layout, or a `layout:` this tool does not speak. Never path-guessed; run `kb migrate` |
| 13 | `migrate` · write verbs | refused on an unsafe state: an uncommitted worktree, or a path outside the base |
| 14 | `init` only | a template left an unrendered `{{placeholder}}` — the template declares a variable this tool does not substitute |

**`kb sync` is the only source of 2–5**, and with `--all` it visits several bases and exits
with the **worst** code any one of them produced, so a 3 means *at least one* base
conflicted, not that all did. Every other verb answers in {0, 1, 2, 10, 11, 13, 14}. Codes
6–9 and 12 are unused.

The double meaning of 2 is worth knowing before scripting against it: a wrapper treating 2 as
"bad arguments" will misread a sync whose local commit failed.

`lint` reports to stdout and exits 0 by default: the report is the interface, and the weekly
job turns criticals into `.kb/pending/` findings. `--ci` is the opt-in that makes criticals
an exit code instead.
