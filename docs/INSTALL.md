# Installing aos — what actually happens

The guide for the *human* about to install. Your agent follows
[`BOOTSTRAP.md`](../BOOTSTRAP.md) (the exact sequence), which loads its harness runtime's
[cheat-sheet](../capabilities/capability-lifecycle/skills/capability-lifecycle/reference/) at the steps that need it; this page tells you what to
expect, what you'll be asked, and what ends up where.

## Before you start

- **Any harness with an agent.** There is no installer program — your own agent does the
  installing, following BOOTSTRAP. Hermes is e2e-verified today; see the
  [support table](../README.md#harnesses). If your harness has no cheat-sheet yet, your
  agent doesn't stop: BOOTSTRAP has it introspect your harness, draft its own
  cheat-sheet, and show it to you before anything lands —
  [contributing that sheet](../CONTRIBUTING.md) is how the next person skips the step.
- **git** — the kit is a clone, and upgrades are `git pull`.
- **[`uv`](https://docs.astral.sh/uv/) (required)** — it carries the `aos-cap`
  bookkeeping tool that owns the install record; your agent offers the official
  installer if it's missing.

## Kick it off

Paste into your agent:

> Clone https://github.com/AlmogBaku/aos.git to ~/aos/upstream, read
> ~/aos/upstream/BOOTSTRAP.md, then set me up.

## What happens next

1. **A welcome, first.** Before anything runs, your agent explains what aos is, what's
   about to happen, and the two promises (your answers stay yours; nothing lands without
   a visible diff) — and takes questions.
2. **Prerequisites + the household.** git and `uv` verified (offered for install if
   missing); the kit clone lands at `~/aos/upstream` (a plain clone — you're one branch
   from contributing, and if you want a fork later your agent offers the one command),
   and `~/aos/personal` is created as your own private repo (a private remote is
   offered, never required).
3. **The lifecycle capability installs itself.** One inline install puts the whole
   lifecycle — install, upgrade, remove, onboard, import, build, contribute, evolve — plus
   the `aos-cap` tool into your harness. From here on, "install X" is a skill, and the lockfile
   (`~/aos/.aos/installs.lock.yaml`, the record of everything materialized) is written by
   the tool, never by hand. Two things ride along:
   - **Two blocks on your own agent.** aos adds two marked passages to your front agent's
     identity file, and nothing else. The first: *before creating a cron job, a standing
     reminder, or any recurring automation, stop and offer to plan it properly*. The second
     is vocabulary — what a capability is, and that your things live in `~/aos` — because
     nothing else in your harness would ever tell it that. What it does **not** add is your
     identity facts: those stay in `MOD.md` (your harness already keeps its own notes about
     you; a second copy would just drift). Agents aos *creates* later are a different case —
     it writes those files whole, so the vocabulary goes in inline.
   - **`skill-creator`, by reference.** Anthropic's skill-authoring skill is linked from
     `~/aos/vendor` (or installed via your harness's plugin mechanism) and kept current —
     never copied into the kit. Best-effort: no network, no plugin, no problem.
4. **The global interview.** Identity, timezone, working hours, sacred time, red lines.
   Your answers become `~/aos/personal/MOD.md` — typed answers in frontmatter, your phrasing and
   nuances in prose. Anything marked secret goes to your harness's secret store; only a
   `{store, key}` reference lands in the file.
5. **Knowledge base setup.** Have a KB already? It gets *adopted* — registered in
   `kb-registry.yaml` with a report of how it diverges from the kit's methodology,
   **nothing rewritten**. Starting fresh? `kb init personal` scaffolds one — by default
   cloning the public template repo, falling back to the templates in your own checkout if
   there's no network. Migrating a big existing KB wholesale is its own guided flow (the
   `kb-import` skill) you can run later.
   - **On an older base**: `kb migrate --base <name>` carries a layout-1 tree to the
     current layout, `git mv` throughout so `git log --follow` still traces every page.
     Then `uv tool uninstall aos-base` — the old command name would otherwise sit on your
     PATH shadowing the new one, and both would appear to work.
   - **No git identity configured?** Nothing blocks. The write lands, `kb lint` reports
     the unattributed commit, and the interview fixes it. Refusing to record your thought
     because we don't know your email would trade the one thing capture cannot lose.
6. **kb installs through the new `capability-install` skill.** The agent reads
   the briefing, checks that no skill name it ships is already taken in your harness,
   renders the skills against your MOD.md (committed in `personal/`), and materializes
   them per the cheat-sheet — renders linked into the right agents, the archiver agent
   created, its schedules registered, kb's `kb` tool installed
   (`uv tool install --from ~/aos/upstream/capabilities/kb/tool aos-kb`).
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
| `install work-tracker` | Briefing read → missing deps recursed → its interview → diff gate → materialize → lockfile |
| `update` | After `git pull`: your hand-edits folded into MOD.md → fresh upstream × MOD.md re-rendered into `personal/` → diff gate |
| "make the steward run at 22:00" | The evolve skill: change applied AND recorded in your MOD.md — survives every upgrade |
| `remove work-tracker` | The lockfile entry walked backwards; your `MOD.md` survives removal |

## Degraded modes, in plain words

Capabilities declare what they need from a host and what happens when it's missing —
installing anyway is fine, silently pretending is not:

- **No cron?** Scheduled work (the nightly steward, the promote pass) becomes a run-card
  you trigger by asking ("run the steward now").
- **`uv` gone after bootstrap?** (it's required to bootstrap) — kb's verbs degrade to
  prose procedures until it's back; the lifecycle's bookkeeping needs it restored.
- **A channel you haven't set up yet is not a missing feature.** What counts is whether
  your harness *can* do the thing (the cheat-sheet answers that), not whether you've wired
  it today: a capability that wants inbound messaging installs on a harness that supports
  it, and you're told what's left to connect. An install stops on a `required` feature only
  when the harness can't express it at all.

## Where your things live

| Thing | Where | Owned by |
|---|---|---|
| Your answers & nuances | `~/aos/personal/MOD.md`, `~/aos/personal/capabilities/*/MOD.md` | **you** — upstream never ships or writes these |
| Your rendered skills (what your harness links to) | `~/aos/personal/capabilities/*/skills/` | **you** — committed by your agent, every upgrade is a reviewable git diff |
| Your KB registry | `~/aos/personal/kb-registry.yaml` | **you** |
| Your KBs | wherever you keep them (each base is its own git repo) | **you** |
| The kit itself | `~/aos/upstream` | upstream — pristine; also the checkout you'd branch from to contribute |
| Referenced third-party skills | `~/aos/vendor` (e.g. `skill-creator`) | their authors — kept current, never copied into the kit |
| Skill links / agents / schedules | your harness's own locations (per cheat-sheet; a skill is a symlink to its one committed render in `personal/`, never a copy) | your agent, tracked in the lockfile |
| Install record | `~/aos/.aos/installs.lock.yaml` (household level) | your agent, machine-local |
| Who you are, per machine | `~/aos/.aos/kb-principal.yml` — written by the `kb` tool on first use | the tool, machine-local |

Hand-editing materialized artifacts is fine — the agent folds your edits back into
MOD.md when it notices (see [USAGE.md](USAGE.md)). Everything yours lives in
`~/aos/personal` — one private repo your agent commits for you; add a private remote
and a new machine is `clone + clone + re-install` away (the lockfile is machine-local, so the install re-creates the links). Nothing personal ever enters the
kit clone or any public remote.
