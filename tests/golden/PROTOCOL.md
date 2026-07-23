# Golden-render protocol — real Hermes, disposable profile

The tier-2 test (RFC-002) run for real, per the project rule: **no simulated harness.**
E2E = create a disposable Hermes profile and tell it to install; the render is checked
structurally, snapshotted, and removed.

## Namespace

Everything the run creates is identifiable and disposable:

- Profiles: `aos-test` (the front agent / install home) and `aos-<agent>` for capability
  agents (e.g. `aos-drainer`, `aos-archiver`).
- Cron jobs: the `aos:<capability>:<schedule-id>` name prefix (cheat-sheet rule).
- KBs: under `tests/.sandbox/kb/` (gitignored) — never a real KB.
- User clone: `tests/.sandbox/aos-clone/` — a clone of this repo seeded with the fixture
  overlay (`tests/fixtures/user-clone/*` copied in, `diff_review` set to `auto-accept`
  for unattended runs — the §5.4 degenerate case, recorded in the global MOD as the spec
  requires; interactive runs keep `always-review`).

## Run

1. **Pre-state**: record `sha256(config.yaml)`, the profile list, root `skills/` listing,
   and root cron job ids (`tests/golden/prestate.sh` → `tests/.sandbox/prestate.txt`).
2. `hermes profile create aos-test`.
3. **Install** — tell the agent (`hermes -p aos-test -z "<prompt>"`, falling back to the
   default profile with the same prompt if the fresh profile has no credentials):

   > You are the Hermes harness agent installing from the aos kit cloned at
   > `<sandbox>/aos-clone`. Read `harnesses/hermes/CHEATSHEET.md` and `docs/BOOTSTRAP.md`
   > there and follow them exactly. The interviews already ran — the overlay files
   > (`MOD.md`, `kb-registry.yaml`, `capabilities/*/MOD.md`) are present in the clone.
   > Your install home (the "front agent") is the `aos-test` profile
   > (`~/.hermes/profiles/aos-test`); create capability agents as `aos-<name>` profiles.
   > Install: kb, onboarding, gtd-capture. Record the lockfile at
   > `<clone>/.aos/installs.lock.yaml`.

   The installer gets **no other context** — capability + cheat-sheet + overlay must
   suffice; that is the test.
4. **Check**: `node tests/golden/check.mjs --live` runs the structural checks against the
   materialized tree (expectations in `tests/golden/expectations/*.yaml`), plus the
   canary check against the pre-state snapshot.
5. **Snapshot**: `node tests/golden/normalize.mjs <paths>` → commit under
   `tests/golden/hermes/<cap>/`. The commit diff is the reviewable render (RFC-002).
   Save the run transcript to `tests/transcripts/`.
6. **Remove**: tell the agent to remove per the cheat-sheet Removal section; verify with
   `prestate.sh` that `~/.hermes` matches pre-state; `hermes profile delete` the test
   profiles.

## Judging (agentic, advisory)

For re-renders, a fresh judge subagent gets old + new snapshots, the capability, the
fixture MOD, and `RUBRIC.md`, and returns `EQUIVALENT | DIVERGENT` per criterion. The
structural checks are the blocking floor; the judge informs the human review.
