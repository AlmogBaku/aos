# The GitHub adapter — a janitor, and a template to copy

A base is one git repo. When more than one person writes to it, two things that were
free for a single user stop being free: somebody has to run the checks, and somebody has
to decide what gets promoted. This adapter answers the first and deliberately leaves the
second open.

## What ships here

- `workflows/kb-janitor.yml` — the deterministic checks, on every push and PR plus a
  weekly run. `base init --audience shared` copies it into a new base's
  `.github/workflows/`; `--no-ci` skips it.

## Why CI, and not a person

**A shared base has no neutral actor.** Whichever household runs the checks is also the
household whose agent reads everybody else's raw material — and that agent holds write
access to shared knowledge. A CI runner holds this base and nothing else: no other
private bases, no messaging tools, no user context. That is a materially smaller blast
radius for the same job.

**It is also the only enforcement a small team will have.** GitHub gates rulesets,
branch protection, and CODEOWNERS to Pro/Team/Enterprise *for private repositories*; the
free plan gets none of them, and gets 2,000 Actions minutes a month. So on the setup a
small team actually has, you cannot block a bad push — you can only fail it loudly,
in front of everyone, every time. That is what this is.

If you *do* have branch protection, use it: require a pull request on the default branch
and keep the agents' identities out of the bypass list. Push to a per-machine branch and
keep one long-lived PR per machine rather than opening one per sync — GitHub's
content-creation limit is 500 requests an hour, and a five-minute timer across a few
machines will find it.

## What the janitor checks

All of it deterministic, all of it already in `base lint`:

- the schema and layout guard, page frontmatter, alias collisions, duplicate titles
- index drift, broken wikilinks, timeline shape, stale seedlings
- the **grants audit** — git authorship against the base's `## Grants` table. This is a
  real check now: every write is its own commit (author = the human principal, committer
  = the acting agent), so nothing is batched under one identity and only `bootstrap` is
  exempt.
- **zero `method: llm` records in a shared base, ever** — the one rule that must never be
  judgment. The exclusion is a list filter, not a confidence threshold.
- unattributed commits: an author outside the `principals:` roster, or a write that
  reached git only through the sync sweep
- left-behind git operation state, which is what silently stalls a sync loop forever

`--ci` turns the report into a verdict: exit 1 on any critical. Findings still print
without failing the run.

## What it does not do

**It does not promote.** Turning raw captures into wiki pages is judgment, and who does
it on a shared base is an open question — see RFC-010. Today that is a household's job,
in one of two shapes the grants table already expresses:

- **Per-principal** (the default): everyone drains only their own captures. `base inbox`
  scopes to the acting principal; `--all` is the override.
- **Designated curator**: one principal holds the wiki write grants and the others
  capture and propose. Simplest to reason about, and the cost is that the curator's agent
  reads everyone's raw material.

Either way, agent writes into a shared base are proposals in `_ops/needs-review/`, never
direct — a human applies them. That is not caution for its own sake: an external
evaluation of memory promotion found *zero of 133 candidates safe to promote
automatically*, and a public audit of one agent-memory store found 97.8% of 10,134
entries were junk, with a single hallucinated fact copied 808 times.

## Using it as a template repository

Copy, do not fork — a fork keeps an upstream relationship pointing at your team's
knowledge, which is not what you want. On GitHub that is **Use this template**.

1. Create the base: `base init <name> --path <dir> --audience shared --sync rebase-5min
   --remote <url>`. The workflow lands in `.github/workflows/`.
2. Add a `principals:` roster to `BASE.yaml` — it maps each member's git author email to
   the subject the Grants table names. Without a roster every write is `user`, which is
   the single-human case.
3. Give each principal their grant rows in `AGENTS.md`, and commit. The roster and the
   table both travel with the repo, so every member sees the same rules.
4. Set `BASE_TOOL_SOURCE` as a repository variable if you want to pin the tool to a tag
   or a fork.

Everyone's own machine still runs `base sync` on its own schedule; nothing here replaces
that.
