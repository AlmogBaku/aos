# Bootstrap: the first five minutes

You are a harness agent setting up aos for your user. There is no installer binary — **you
are the installer** (ARCHITECTURE §5.1). Follow this sequence exactly. Steps are marked
**[D]** (mechanical — do it precisely, verify, record) or **[A]** (judgment — think, then
show your work).

Before anything: read `harnesses/<your-harness>/CHEATSHEET.md`. If no cheat-sheet exists for
your harness, stop and tell the user — do not improvise a materialization scheme.

## 0. Ground rules (bind every step below)

- **The diff gate is never optional.** Nothing lands in the harness until the user has seen
  the full diff of what you are about to write and approved it (§5.4).
- **You never write** any `MOD.md` except through the onboarding interview, and you never
  edit shipped capability files in the clone — personalization lives only in the overlay
  (§3.1) and the materialized artifacts.
- **Everything you materialize is recorded** in `.aos/installs.lock.yaml` with its path and
  sha256 (schedules by job id under `schedules_owned`). No lockfile record, no artifact.
- Harness-owned files (e.g. Hermes `config.yaml`, `cron/jobs.json`) are touched only through
  the harness's own CLI, per the cheat-sheet.

## 1. [D] Clone + state

1. Clone the kit to `~/aos` (or confirm it's already there and clean: `git -C ~/aos status`).
2. Verify `harnesses/<your-harness>/CHEATSHEET.md` exists.
3. Create `.aos/` in the clone with an empty lockfile:

```yaml
# ~/aos/.aos/installs.lock.yaml
version: 1
installs: {}
```

`.aos/` is machine-local and already gitignored. Whether the user tracks their overlay in a
private fork or keeps it local is their choice (RFC-005) — don't decide it for them; if they
ask, present both options neutrally.

## 2. [A] Global interview → root MOD.md

Run the **onboarding** capability's own interview: read
`capabilities/onboarding/ONBOARDING.md` and follow its script conversationally — identity,
timezone, working hours, sacred time, red lines. Then:

- **[D]** validate every answer against the question list (typed frontmatter is the schema);
- **[D]** any `secret: true` answer: value → harness secret store per the cheat-sheet,
  reference `{store, key}` → MOD.md;
- **[A]** write `~/aos/MOD.md` — typed answers in frontmatter, prose nuances in the body.

Re-running later is safe: only missing or `re_ask`-triggered questions are asked again;
`--refresh` re-asks everything and shows a diff before writing (§3.2).

## 3. [A] KB setup → kb-registry.yaml

Ask the user about their knowledge bases:

- **Existing KB(s)** → for each, run the kb capability's `adopt` skill
  (`capabilities/kb/skills/adopt/SKILL.md`): register it in `~/aos/kb-registry.yaml` and
  lint-report divergence from its methodology — **never rewrite the user's KB**.
- **No KB yet** → run the `init` skill: `kb init personal` scaffolds a private default KB
  from `capabilities/kb/methodologies/karpathy-3layer/init/` and registers it.

Either way this writes `~/aos/kb-registry.yaml` (user-owned, overlay family).

## 4. [D] Install the two root capabilities

The installer needs kb and onboarding installed; their interviews already ran above, so
their install steps are carried here inline (this breaks the chicken-and-egg):

**onboarding** (`capabilities/onboarding/`):
1. [D] Read its `CAPABILITY.md`; check `depends.host` against the cheat-sheet Feature notes.
2. [A] Transform: original skills × root `MOD.md` → personalized copies (fill `{{mod: …}}`
   slots; leave unfilled slots intact).
3. [A] Materialize per the cheat-sheet: its skills are `used_by: [main]` → the front agent's
   skills location, tagged `x-aos-origin: onboarding@<version>`.
4. [D] Diff gate → write → record in lockfile.

**kb** (`capabilities/kb/`):
1. [D] Read its `CAPABILITY.md`; host check (`cron: preferred` — if absent, note the
   degraded mode for each schedule, per cheat-sheet).
2. [A] Transform its skills (route, authz-check, init, adopt) with `MOD.md` +
   `kb-registry.yaml` context.
3. [A] Materialize: `main`-scoped skills to the front agent; create the **archiver** agent
   per `agents/archiver.agent.yaml` and the cheat-sheet's agent mapping; archiver-scoped
   skills (methodology lint) into the archiver's workspace.
4. [A] Register schedules (nightly promote, weekly lint, sync) on the archiver per the
   cheat-sheet's schedule mapping — single-owner rule applies (§5.5).
5. [A] Register KB zones: append this capability's grant rows to each target KB's
   `AGENTS.md` `## Grants` table (drafted by you, approved by the user — kb-authorization
   §3.3).
6. [D] Diff gate → write → record artifacts + hashes + `schedules_owned`.

## 5. Done

Tell the user what was installed, where, and any degraded modes in effect. Everything after
this is on demand:

- `install <capability>` — read its CAPABILITY.md, recurse into missing deps, interview,
  transform, diff gate, materialize, record (design/install-flow.md §2).
- `update` — after `git pull`: backup → LLM merge (new template × current install × MOD.md)
  → diff gate → record (§3).
- `remove <capability>` — walk the lockfile entry backwards per the cheat-sheet's Removal
  section; MOD.md is never deleted (§4).
- User hand-edits to installed artifacts are normal — capture them back into MOD.md when you
  notice them (`sync-mod`, §3.3 round-trip).
