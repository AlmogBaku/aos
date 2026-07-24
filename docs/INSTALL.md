# Installing aos — what actually happens

The guide for the *human* about to install. Your agent follows
[`BOOTSTRAP.md`](../BOOTSTRAP.md) (the exact sequence), which loads its harness runtime's
[cheat-sheet](../capabilities/capability-lifecycle/harnesses/) at the steps that need it; this page tells you what to
expect, what you'll be asked, and what ends up where.

## Before you start

- **Any harness with an agent.** There is no installer program — your own agent does the
  installing, following BOOTSTRAP. Hermes is e2e-verified today; see the
  [support table](../README.md#install). If your harness has no cheat-sheet yet, your
  agent doesn't stop: BOOTSTRAP has it introspect your harness, draft its own
  cheat-sheet, and show it to you before anything lands —
  [contributing that sheet](../CONTRIBUTING.md) is how the next person skips the step.
- **git** — the kit is a clone, and upgrades are `git pull`.
- **[`uv`](https://docs.astral.sh/uv/) (required)** — it carries the `aos-lock`
  bookkeeping tool that owns the install record; your agent offers the official
  installer if it's missing.

## Kick it off

Paste into your agent:

> Clone https://github.com/AlmogBaku/aos to ~/aos, read ~/aos/BOOTSTRAP.md, then set me up.

## What happens next

1. **A welcome, first.** Before anything runs, your agent explains what aos is, what's
   about to happen, and the two promises (your answers stay yours; nothing lands without
   a visible diff) — and takes questions.
2. **Prerequisites + clone.** git and `uv` verified (offered for install if missing);
   the clone lands at `~/aos`.
3. **The lifecycle capability installs itself.** One inline install puts the
   install/upgrade/remove/evolve skills and the `aos-lock` tool into your harness —
   from here on, "install X" is a skill, and the lockfile
   (`.aos/installs.lock.yaml`, the record of everything materialized) is written by
   the tool, never by hand.
4. **The global interview.** Identity, timezone, working hours, sacred time, red lines.
   Your answers become `~/aos/MOD.md` — typed answers in frontmatter, your phrasing and
   nuances in prose. Anything marked secret goes to your harness's secret store; only a
   `{store, key}` reference lands in the file.
5. **Knowledge base setup.** Have a KB already? It gets *adopted* — registered in
   `kb-registry.yaml` with a report of how it diverges from the kit's methodology,
   **nothing rewritten**. Starting fresh? `base init personal` scaffolds one from
   templates. Migrating a big existing KB wholesale is its own guided flow (kb's
   `import` skill) you can run later.
6. **Both installs run through the new `capability-installer` skill.** For each, the agent reads
   the briefing, personalizes the skills with your MOD.md, and materializes them per the
   cheat-sheet — skills into the right agents, the archiver agent created, its schedules
   registered, kb's `base` tool installed
   (`uv tool install --from ~/aos/capabilities/kb/tool aos-base`).
7. **Done.** The agent tells you what was installed, where, and any degraded modes in
   effect — specifically, not vaguely.

> [!IMPORTANT]
> **You approve every write.** Before anything lands in your harness, the agent shows
> the full diff and waits. This is the spec's diff gate — if your agent skips it,
> that's a bug, not a feature.

## After bootstrap

Everything else is a sentence, on demand:

| You say | What happens |
|---|---|
| `install gtd-capture` | Briefing read → missing deps recursed → its interview → diff gate → materialize → lockfile |
| `update` | After `git pull`: your hand-edits folded into MOD.md → backup → fresh upstream × MOD.md re-applied → diff gate |
| "make the drain run at 22:00" | The evolve skill: change applied AND recorded in your MOD.md — survives every upgrade |
| `remove gtd-capture` | The lockfile entry walked backwards; your `MOD.md` survives removal |

## Degraded modes, in plain words

Capabilities declare what they need from a host and what happens when it's missing —
installing anyway is fine, silently pretending is not:

- **No cron?** Scheduled work (nightly drain, promote) becomes a run-card you trigger by
  asking ("drain the inbox now").
- **`uv` gone after bootstrap?** (it's required to bootstrap) — kb's verbs degrade to
  prose procedures until it's back; the lifecycle's bookkeeping needs it restored.
- A `required` host feature that's absent stops that capability's install with an
  explanation.

## Where your things live

| Thing | Where | Owned by |
|---|---|---|
| Your answers & nuances | `~/aos/MOD.md`, `~/aos/capabilities/*/MOD.md` | **you** — upstream never ships or writes these |
| Your KB registry | `~/aos/kb-registry.yaml` | **you** |
| Your KBs | wherever you keep them (each base is its own git repo) | **you** |
| Materialized skills/agents/schedules | your harness's own locations (per cheat-sheet) | your agent, tracked in the lockfile |
| Install record | `~/aos/.aos/installs.lock.yaml` | your agent, machine-local |

Hand-editing materialized artifacts is fine — the agent folds your edits back into
MOD.md when it notices (see [USAGE.md](USAGE.md)). Whether to keep your overlay in a
private fork or local-only is your call (RFC-005 tracks the recommendation); the
agent won't decide for you.
