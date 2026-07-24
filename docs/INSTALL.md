# Installing aos — what actually happens

The guide for the *human* about to install. Your agent follows
[`BOOTSTRAP.md`](../BOOTSTRAP.md) (the exact sequence) and its harness's
[cheat-sheet](../harnesses/); this page tells you what to expect, what you'll be asked,
and what ends up where.

## Before you start

- **A supported harness.** Hermes today; see the [support table](../README.md#install).
  If your harness has no `harnesses/<name>/CHEATSHEET.md`, the installer will stop and
  say so rather than improvise — [contributing a cheat-sheet](../CONTRIBUTING.md) is how
  a new harness gets supported.
- **git** — the kit is a clone, and upgrades are `git pull`.
- **[`uv`](https://docs.astral.sh/uv/) (optional)** — installs kb's `base` tool. Without
  it, kb still works: the skills fall back to prose procedures (slower, LLM-driven).

## Kick it off

Paste into your agent:

> Clone https://github.com/AlmogBaku/aos to ~/aos, read
> ~/aos/harnesses/&lt;your-harness&gt;/CHEATSHEET.md and ~/aos/BOOTSTRAP.md, then set me up.

## What happens next

1. **Clone + bookkeeping.** The agent clones to `~/aos` and creates
   `.aos/installs.lock.yaml` — the record of everything it will ever materialize.
2. **The global interview.** Identity, timezone, working hours, sacred time, red lines.
   Your answers become `~/aos/MOD.md` — typed answers in frontmatter, your phrasing and
   nuances in prose. Anything marked secret goes to your harness's secret store; only a
   `{store, key}` reference lands in the file.
3. **Knowledge base setup.** Have a KB already? It gets *adopted* — registered in
   `kb-registry.yaml` with a report of how it diverges from the kit's methodology,
   **nothing rewritten**. Starting fresh? `base init personal` scaffolds one from
   templates. Migrating a big existing KB wholesale is its own guided flow (kb's
   `import` skill) you can run later.
4. **The two root capabilities install: kb and onboarding.** For each, the agent reads
   the briefing, personalizes the skills with your MOD.md, and materializes them per the
   cheat-sheet — skills into the right agents, the archiver agent created, its schedules
   registered, kb's `base` tool installed
   (`uv tool install --from ~/aos/capabilities/kb/tool aos-base`).
5. **Done.** The agent tells you what was installed, where, and any degraded modes in
   effect.

> [!IMPORTANT]
> **You approve every write.** Before anything lands in your harness, the agent shows
> the full diff and waits. This is the spec's diff gate — if an installer skips it,
> that's a bug, not a feature.

## After bootstrap

Everything else is a sentence, on demand:

| You say | What happens |
|---|---|
| `install gtd-capture` | Briefing read → missing deps recursed → its interview → diff gate → materialize → lockfile |
| `update` | After `git pull`: backup → merge (new template × your install × your MOD.md) → diff gate |
| `remove gtd-capture` | The lockfile entry walked backwards; your `MOD.md` survives removal |

## Degraded modes, in plain words

Capabilities declare what they need from a host and what happens when it's missing —
installing anyway is fine, silently pretending is not:

- **No cron?** Scheduled work (nightly drain, promote) becomes a run-card you trigger by
  asking ("drain the inbox now").
- **No `uv`?** kb's verbs run as prose procedures instead of the deterministic tool.
- A `required` host feature that's absent stops that capability's install with an
  explanation.

## Where your things live

| Thing | Where | Owned by |
|---|---|---|
| Your answers & nuances | `~/aos/MOD.md`, `~/aos/capabilities/*/MOD.md` | **you** — upstream never ships or writes these |
| Your KB registry | `~/aos/kb-registry.yaml` | **you** |
| Your KBs | wherever you keep them (each base is its own git repo) | **you** |
| Materialized skills/agents/schedules | your harness's own locations (per cheat-sheet) | the installer, tracked in the lockfile |
| Install record | `~/aos/.aos/installs.lock.yaml` | the installer, machine-local |

Hand-editing materialized artifacts is fine — the agent folds your edits back into
MOD.md when it notices (see [USAGE.md](USAGE.md)). Whether to keep your overlay in a
private fork or local-only is your call (RFC-005 tracks the recommendation); the
installer won't decide for you.
