# Golden-render protocol — real Hermes, disposable profile

The tier-2 test (RFC-002) run for real, per the project rule: **no simulated harness.**
E2E = create a disposable Hermes profile and tell it to install; the render is checked
structurally, snapshotted, and removed.

## Namespace

Everything the run creates is identifiable and disposable:

- Profiles: `aos-test` (the front agent / install home) and `aos-<agent>` for capability
  agents (e.g. `aos-drainer`, `aos-archiver`).
- Cron jobs: the `aos:<capability>:<schedule-id>` name prefix (contract rule).
- KBs: under `tests/.sandbox/kb/` (gitignored) — never a real KB.
- The household: `tests/.sandbox/aos-home/` — `upstream/` (a clone of this repo),
  `personal/` (a git-init'd repo seeded with the fixture overlay at mirrored paths:
  `tests/fixtures/personal/*` copied in, `diff_review` set to `auto-accept` for
  unattended runs — the §5.4 degenerate case, recorded in the global MOD as the spec
  requires; interactive runs keep `always-review`), and `.aos/` (created by
  `aos-lock --home <sandbox>/aos-home init`).

## Run

1. **Pre-state**: record `sha256(config.yaml)`, the profile list, root `skills/` listing,
   and root cron job ids (`tests/golden/prestate.sh` → `tests/.sandbox/prestate.txt`).
   Also clear leftovers from a previous run inside the `aos-*` namespace (e.g. a renamed
   `scripts/aos-kb-sync.sh.unused` in a profile) — a sentinel must test what *this*
   install wrote, never debris that survived the last one.
2. `hermes profile create aos-test`.
3. **Install** — tell the agent (`hermes -p aos-test -z "<prompt>"`, falling back to the
   default profile with the same prompt if the fresh profile has no credentials):

   > You are the Hermes harness agent installing from the aos kit. The aos household
   > is at `<sandbox>/aos-home` (not the default `~/aos`): the kit clone is
   > `aos-home/upstream`, the user's personal repo is `aos-home/personal`. Read
   > `upstream/BOOTSTRAP.md` and follow it exactly. The interviews already ran — the
   > overlay files (`MOD.md`, `kb-registry.yaml`, `capabilities/*/MOD.md`) are present
   > in `personal/` at mirrored paths. Your install home (the "front agent") is the
   > `aos-test` profile (`~/.hermes/profiles/aos-test`); create capability agents as
   > `aos-<name>` profiles. Renders land in `personal/` and skills are symlinked per
   > the contract. Install: kb (gtd-capture comes later, as its own prompt — see the
   > Day-N step). The lockfile lives at `aos-home/.aos/installs.lock.yaml`
   > (`aos-lock --home <sandbox>/aos-home`).

   The installer gets **no other context** — BOOTSTRAP + the capability-lifecycle
   contract + capability + cheat-sheet + overlay must suffice; that is the test.
   Bootstrap installs capability-lifecycle (nine skills — the interview engine among
   them, so there is no separate onboarding install) and kb. The name gate
   (`aos-lock skills … --check`) runs before each install; a fresh `aos-test` profile has
   no skills of its own, so it must come back clean.

   **Day-N step** (the seam this exists to prove): a SEPARATE, fresh prompt with no
   bootstrap context — `hermes -p aos-test -z "install gtd-capture from the aos household
   at <sandbox>/aos-home"` (default-profile fallback as above) — must trigger the
   materialized `capability-install` skill and complete the install.

4. **Check**: `node tests/golden/check.mjs --live` runs the structural checks against the
   materialized tree (expectations in `tests/golden/expectations/*.yaml`), plus the
   canary check against the pre-state snapshot.
5. **Snapshot**: `node tests/golden/normalize.mjs <paths>` → commit under
   `tests/golden/hermes/<cap>/`. The commit diff is the reviewable render (RFC-002).
   Save the run transcript to `tests/transcripts/`.
   **Evolve step (after the snapshot — it mutates install state)**: a fresh prompt —
   "change gtd-capture's drain schedule to 22:00" — must route through
   `capability-evolve`: the cron job changes, the change lands in
   `personal/capabilities/gtd-capture/MOD.md` (auto-committed by the persist hook), and
   `aos-lock verify` stays clean. **Note when running via the default-profile fallback:**
   the fallback agent does not carry the materialized skills in context, so the prompt
   must name the skill path explicitly (`~/.hermes/profiles/aos-test/skills/
   capability-evolve/SKILL.md`) — otherwise it edits the cron
   natively and skips the ledger, which is a fallback artifact, not a skill failure.
   Capture mode is then the second half of the test: fold the existing change into the
   ledger and confirm the persist commit.
6. **Remove**: tell the agent to remove per the cheat-sheet Removal section; verify with
   `prestate.sh` that `~/.hermes` matches pre-state; `hermes profile delete` the test
   profiles.

## Judging (agentic, advisory)

For re-renders, a fresh judge subagent gets old + new snapshots, the capability, the
fixture MOD, and `RUBRIC.md`, and returns `EQUIVALENT | DIVERGENT` per criterion. The
structural checks are the blocking floor; the judge informs the human review.
