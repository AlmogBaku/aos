---
name: kb
description: "Explains how the user's knowledge bases are laid out and which kb skill handles a given job — the tree, the pending queue, expiry, links, base health, maintenance. Use when the user asks how their knowledge base works, what state a base is in, why something was or was not kept, or wants base maintenance run, and no narrower kb skill matches. Do NOT use to file something the user just said (that is kb-capture), to answer a question from stored knowledge (that is kb-recall), or to pick a destination base for a write already in hand (that is kb-route)."
---

# kb — the base system in one page

**Files are the database.** A base is a git repo of markdown; every index is a rebuildable
derivative; the `kb` tool never calls a model — mechanics are its, judgment is yours.

```
<base>/
├── .kb/          tool-managed: base.yml · state/<principal>.yml · pending/ · work/ · cache/
├── AGENTS.md     the contract — read before any non-trivial write
├── README.md     the base explained to a human
├── index.md      the map, one line per page
├── _raw/         source material, flat and immutable once ingested
└── entities/ concepts/ projects/ profile/    wiki pages — current truth only
```

`.kb/`'s three subdirectories have three tests: **pending/** waiting on someone ·
**work/** a procedure in progress · **cache/** rebuildable, gitignored.

## The queue

`.kb/pending/` is the only queue — one file per item, `waits_on:` naming who is blocked
(`agent` or `human`) and `kind:` naming what it is (`capture` `refusal` `conflict` `entity`
`finding`). A queue *file* is only justified when the work has no artifact of its own;
everything else is a query.

Two reads, and picking the wrong one returns an empty list with exit 0 rather than an error:

- **`kb inbox`** — *your* ingest work: `waits_on: agent` only, scoped to the acting principal.
  This is the nightly promote pass's read. On a base several people write to, that scoping is
  the point: the unfiltered view would hand you everyone's captures, so the same item gets
  processed once per person and somebody else's raw material enters your context. `--all` is
  the designated curator's path, not the default.
- **`kb pending list --where waits_on=human`** — the *human's* drain queue. `inbox` cannot show
  these at all (it filters to `agent`), so an agent looking for findings to surface, or a
  person asking what is waiting on them, needs this form.

For everything else, query rather than queue: `kb find --where type=company --where
tags=active` over frontmatter (list fields match by membership), `kb search` for full text.
The tool does the date arithmetic, so nobody computes "seven days before Tuesday" by hand and
gets it silently wrong — but **quote any comparison**, because a bare `<` is shell
redirection:

```
kb find --where 'expires<today+7d'
```

A field a base does not use returns zero matches with exit 0, so check the base's own
`frontmatter.extensions` before filtering on something like `due` or `status`.

## Lifetime

kb knows exactly one thing about how long a page lives: **`expires:`**. Without it the page
lives forever, and most pages never carry one. `_raw/` never expires — answers cite pages,
pages cite raw.

Both ways a page leaves are destructive, so both get looked at before and after:

- **Expired** → `kb --base <name> prune --dry-run` to see the list, then the same command
  without `--dry-run`, then read what it reports as deleted. Git is the undo, but an undo
  nobody knows they need is no undo, so the point of the dry run is to notice a page you did
  not expect on that list.
- **Stopped mattering** → that is a judgment, not a date, so it leaves through
  `kb --base <name> archive <page> --reason "<why>"` — a `git rm` plus an attributed commit.
  Confirm the commit landed (`kb history`) rather than assuming it did. The tool will archive
  with **no** `--reason` and destroy the page anyway; if you cannot state the reason, you have
  not earned the archive, so don't run the command.

**Name `--base` explicitly on both, every time.** A bare `kb prune` resolves a base by walking
up from the current directory and then falling back to the *registry default* — so run from
anywhere else, it deletes from a base you were not thinking about, and reports success. The
dry run and the real run resolve independently, so without an explicit `--base` they are not
even guaranteed to be talking about the same base.

## Links

`[[wikilink]]` inside a base. Pages move constantly — promotion files them into zones,
agents create deeper subdirectories — and a wikilink survives that where a path-bearing
link breaks in every page that wrote it. The link graph is one regex because of it, and an
unresolved `[[Acme Corp]]` is a designed signal meaning "mentioned, not yet a page".
Anything outside the base is an ordinary markdown link, which the graph ignores by
construction.

## Which skill

| Job | Skill |
|---|---|
| The user just said something worth keeping | `kb-capture` |
| Pick the destination base for a write in hand | `kb-route` |
| Answer "what do I know about X?" | `kb-recall` |
| Create a new base | `kb-init` |
| Register a tree that already exists | `kb-adopt` |
| Bulk-migrate another KB's content | `kb-import` |

## Authority

- Freely: read what you are granted; capture; `search` / `find` / `links` / `lint`.
- Report-only: lint findings and sync conflicts land in `.kb/pending/` as
  `waits_on: human`. The human drains that, never you.
- Ask first: any page in a **shared** base, zone or type changes (`.kb/base.yml` is
  owner-approved), anything under `profile/`, and flipping `verified`.
- **Destroys things — never on your own initiative:** `kb prune` runs from the weekly
  schedule, which dry-runs it first; if you are running it because a user asked, dry-run it
  and show them the list. `kb archive` has no scheduled owner at all — it is a judgment that
  a page stopped mattering, so it is the user's call and you propose it, with the reason you
  would put in `--reason`.

Deeper: [reference/lifecycle.md](reference/lifecycle.md) (page schema, current truth,
trust) · [reference/grants.md](reference/grants.md) (the one ACL) ·
[reference/wiring.md](reference/wiring.md) (schedules and degraded modes).
