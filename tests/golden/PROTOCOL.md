# Golden-render protocol — real Hermes, disposable profile

The tier-2 test (RFC-002) run for real, per the project rule: **no simulated harness.**
E2E = create a disposable Hermes profile and tell it to install; the render is checked
structurally, snapshotted, and removed.

## Namespace

Everything the run creates is identifiable and disposable:

- Profiles: `aos-test` (the front agent / install home) and `aos-<agent>` for capability
  agents (`aos-archiver` for kb, `aos-steward` for work-tracker).
- Cron jobs: the `aos:<capability>:<schedule-id>` name prefix (contract rule).
- KBs: under `tests/.sandbox/kb/` (gitignored) — never a real KB.
- The household: `tests/.sandbox/aos-home/` — `upstream/` (a clone of this repo),
  `personal/` (a git-init'd repo seeded with the fixture overlay at mirrored paths:
  `tests/fixtures/personal/*` copied in, `diff_review` set to `auto-accept` for
  unattended runs — the §5.4 degenerate case, recorded in the global MOD as the spec
  requires; interactive runs keep `always-review`), and `.aos/` (created by
  `aos-cap --home <sandbox>/aos-home init`).

## Run

1. **Pre-state**: record `sha256(config.yaml)`, the profile list, root `skills/` listing,
   and root cron job ids (`tests/golden/prestate.sh` → `tests/.sandbox/prestate.txt`).
   Also clear leftovers from a previous run inside the `aos-*` namespace (e.g. a renamed
   `scripts/aos-kb-sync.sh.unused` in a profile) — a sentinel must test what *this*
   install wrote, never debris that survived the last one.
2. `hermes profile create aos-test`, then give it a working provider — a fresh profile has
   only `model.default` and fails with `Invalid length for parameter modelId`. Copy a
   working profile's `config.yaml` (`model.provider`, `base_url`, and the `terminal`/`file`/
   `skills`/`cronjob` toolsets); the normalizer skips `config.yaml`, so nothing private
   reaches the snapshot. Capability agents (`aos-archiver`, `aos-steward`) need the same.

   **Copy the credential env too, not just `config.yaml`.** A freshly-created profile writes
   its own `.env`, which SHADOWS the root's — and the root's is where the provider credentials
   live (`AWS_PROFILE`/`AWS_REGION` for bedrock, plus `SSL_CERT_FILE`/`REQUESTS_CA_BUNDLE`).
   Without them Hermes blocks forever on `auth.lock` resolving credentials it cannot see:
   **zero output, zero CPU, `futex_do_wait`, nothing in any log.** That reads exactly like a
   provider outage and is not one — it cost three abandoned runs on 2026-08-01 before
   `ps -o wchan` named the lock. Copy the lines, then smoke-test with
   `hermes -p aos-test -z "Reply with exactly: READY"` before spending a real install on it.

   Also configure a git identity in the seeded `personal/` repo
   (`git -C <sandbox>/aos-home/personal config user.name/user.email` — the fixture persona
   is Dana Fixture): the persist hook commits as the user, and the agent correctly refuses
   to invent an identity.

   **Export `AOS_PRINCIPAL_ID=dana@example.com` for the whole run**, matching that persona.
   Pinned for the same reason `tools/check.sh` and `ci.yml` pin it: "who ran the e2e" is not
   a property of the install. Without it the tool synthesizes `<user>@<host>.local` from
   `getpass` and `socket` and lands whoever ran it in a committed snapshot — which is
   exactly what happened once. The normalizer now redacts that shape too, but the pin is
   the fix at the source and the normalizer is the backstop. The synthesis path itself stays
   covered by `tests/tool/test_kb.py`, which asserts the `.local` suffix directly, so
   pinning here moves that coverage to where the subject is the tool rather than the
   operator — it does not drop it.
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
   > the contract. Install: kb (work-tracker comes later, as its own prompt — see the
   > Day-N step). The lockfile lives at `aos-home/.aos/installs.lock.yaml`
   > (`aos-cap --home <sandbox>/aos-home`).

   The installer gets **no other context** — BOOTSTRAP + the capability-lifecycle
   contract + capability + cheat-sheet + overlay must suffice; that is the test.
   Bootstrap installs capability-lifecycle (ten skills — the interview engine among
   them, so there is no separate onboarding install) and kb. The name gate
   (`aos-cap skills … --check`) runs before each install; a fresh `aos-test` profile has
   no skills of its own, so it must come back clean.

   **Day-N step** (the seam this exists to prove): a SEPARATE, fresh prompt with no
   bootstrap context — `hermes -p aos-test -z "install work-tracker from the aos household
   at <sandbox>/aos-home"` (default-profile fallback as above) — must trigger the
   materialized `capability-install` skill and complete the install.

4. **Check**: `uv run --project tools/aos_lint python -m aos_lint.golden.check --live` runs the structural checks against the
   materialized tree (expectations in `tests/golden/expectations/*.yaml`), plus the
   canary check against the pre-state snapshot.
5. **Snapshot**: `uv run --project tools/aos_lint python -m aos_lint.golden.normalize <paths>` → commit under
   `tests/golden/hermes/<cap>/`. The commit diff is the reviewable render (RFC-002).
   Save the run transcript to `tests/transcripts/`.

   **Re-rendering instead of re-running.** A prose fix to a `{{mod}}`-slot-free skill can be
   re-rendered into the snapshot with `aos-cap render` rather than costing a whole live run —
   the render is a pure function of source + version for those skills. Two conditions, both
   non-negotiable: prove it first by rendering an *untouched* skill and confirming byte
   identity with the committed snapshot, and pipe the output through the normalizer (skipping
   it leaves un-normalized values that the next real run silently flips back). Record which
   files came in that way, here or in the transcript. `aos_lint.golden.check` asserts the snapshot equals
   what the normalizer produces, which catches the second mistake but not the first. Anything
   an agent *decided* — placement, links, schedules, context blocks — only a live run can
   attest.

   Done this way on 2026-07-25 for the nine `capability-lifecycle` skills, to carry two prose
   fixes found in review (`tests/transcripts/2026-07-25-skill-identity-e2e-hermes.md`).
   **Evolve step (after the snapshot — it mutates install state)**: a fresh prompt —
   "change work-tracker's steward hour to 22:00" — must route through
   `capability-evolve`: the cron job changes, the change lands in
   `personal/capabilities/work-tracker/MOD.md` (auto-committed by the persist hook), and
   `aos-cap verify` stays clean. **Note when running via the default-profile fallback:**
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
