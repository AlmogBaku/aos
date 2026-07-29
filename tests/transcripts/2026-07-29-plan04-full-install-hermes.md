# Live e2e — 2026-07-29, Hermes v0.19.0, disposable `aos-test` namespace

The tier-2 run owed since PR #5, and the first covering LAYOUT 2, the `kb` command,
work-tracker, and `metadata.aos.origin`. **A real install, never simulated.**

## Setup

- Household: `tests/.sandbox/aos-home` — `upstream/` a clone of `kb/v2-layout2`,
  `personal/` git-init'd and seeded from `tests/fixtures/personal/` (Dana Fixture,
  `diff_review: auto-accept` for an unattended run — the §5.4 degenerate case),
  `.aos/` from `aos-lock init`.
- Bases under `tests/.sandbox/kb/`; registry paths rewritten to absolute sandbox paths.
- Profile `aos-test` created fresh; provider config copied from a working profile (a bare
  profile fails with `Invalid length for parameter modelId`). Smoke-tested before use.
- Prestate canaries recorded (`prestate.sh`).

## Three prompts, deliberately separate

1. **Bootstrap** — "read BOOTSTRAP.md and follow it exactly", install capability-lifecycle
   then kb, work-tracker explicitly deferred. The installer got BOOTSTRAP + the capability +
   the cheat-sheet + the overlay and **nothing else**; that is the test.
2. **Day-N** — a fresh prompt with no bootstrap context: `install work-tracker from the aos
   household at <sandbox>`. This is the seam the test exists to prove: it must trigger the
   *materialized* `capability-install` skill.
3. **Transform** — fill the `{{mod: action_format}}` slot from MOD.md (see Findings).

## What the install got right unprompted

- **All four of work-tracker's silent-if-missed base changes**: `actions: {kind: wiki}` AND
  `action` in `types:` (either missing makes the directory invisible to every verb at exit 0),
  all eight `frontmatter.extensions`, and **`index.md` on both grant rows** — the object Plan
  03 had to find by code review. Each edit carried a comment naming `work-tracker@0.1.0`.
- The base's registry `name` is literally `commitments`, which `--base` matches and nothing else.
- `47 22 * * *` on the steward's cron: the fixture's `steward_hour: 22:47` reached the schedule.
- `wt-steward` linked into the steward profile **only**; the three conversational skills on the
  front agent. The `used_by` anti-pollution rule, observed.
- The sync wrapper pins `AOS_REGISTRY`, `AOS_HOME` and `AOS_AGENT=agent:archiver` — a bare
  `kb sync` would have silently no-op'd.
- 22 skills, 4 schedules, 3 lockfile entries, 25 recorded links.

## Findings the run produced (both fixed)

1. **The 🦜 sentinel could not be carried: work-tracker shipped ZERO `{{mod}}` slots** while
   declaring ten onboarding answers. The `capability-review` pass had called this a judgment
   call; the e2e made it a fact — the user's confirmation preference had nowhere to land.
   Fixed by adding `action_format` to `wt-capture` and slots for `followup_cadence` /
   `retention_days` in the steward's two hardcoded windows. The re-render then carried both
   halves of the MOD: the typed answer (`verb-first`) *and* the prose nuance (the parrot,
   nothing else, never echo).
2. **The sync-wrapper sentinel looked in the wrong place.** It expected a profile-level copy;
   the cheat-sheet sends `--script` files to `~/.hermes/scripts/`, which is the only place
   Hermes reads them, and the install obeyed the contract. The expectation was the stale side.

## Removal — walked from the lockfile, and exact

The removal *agent* stalled (~20 min, no output) and was stopped; removal was then completed
deterministically from the lockfile record, which is the honest test of whether that record is
sufficient. It was: 25 links unlinked, 4 jobs deleted, the wrapper script removed, three
profiles deleted, three lockfile entries removed — **no guessing at any step**.

- `prestate.sh` after removal is **byte-identical** to before: `~/.hermes` outside `aos-*` was
  never touched, at any checkpoint.
- **User data survived**: three KB bases, all three `MOD.md` files, and `kb-principal.yml`
  left in place rather than assumed (removal *offers*, never assumes).
- `~/ai-kb` untouched throughout — mtime still 2026-07-04.

## Results

- `node tests/golden/check.mjs --live full-install` → **0 failures**
- `node tests/golden/check.mjs` (snapshot mode) → **0 failures**
- Snapshots regenerated from this run: 139 files, 1.3MB. `upstream/` and `vendor/` are now
  excluded — the first is a clone of this repo (its planted lint violations failed the linter
  on the copy), the second a third party's (token-shaped example strings tripped the secret
  scanner). Neither is an install artifact.
- `bash tools/check.sh` → all tiers green.
