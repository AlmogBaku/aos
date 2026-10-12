# Golden-render protocol — real Hermes, disposable profile

The tier-2 test (RFC-002) run for real, per the project rule: **no simulated harness.**
E2E = create a disposable Hermes profile and tell it to install; the render is checked
structurally, snapshotted, and removed.

## Namespace

Everything the run creates is identifiable and disposable:

- Profiles: `aos-test` (the front agent / install home) and `aos-<agent id>` for capability
  agents (`aos-archiver` for kb, `aos-steward` for work-tracker) — named explicitly in both
  install prompts. The computed agent names (`kb-archiver`, `wt-steward`) can be a real
  profile on a dogfooding machine, and the contract *adopts* a profile that carries an
  `aos:<capability>:` job, so an unnamed mapping lets an install adopt the operator's own.
- Cron jobs: the `aos:<capability>:<schedule-id>` name prefix (contract rule).
- KBs: under `tests/.sandbox/kb/` (gitignored) — never a real KB.
- The household: `tests/.sandbox/aos-home/` — `upstream/` (a clone of this repo),
  `personal/` (a git-init'd repo seeded with the fixture overlay at mirrored paths:
  `tests/fixtures/personal/*` copied in, `diff_review` set to `auto-accept` for
  unattended runs — the §5.4 degenerate case, recorded in the global MOD as the spec
  requires; interactive runs keep `always-review`), and `.aos/` (machine state: seeded
  with `tests/fixtures/.aos/kb-registry.yaml` — the registry is machine-local, not
  overlay, so it never goes in `personal/` — and given its lockfile by the install's own
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

   **Pin the household and the identity in every profile's `.env`** — `aos-test` before
   the install, `aos-archiver`/`aos-steward` the moment the install creates them (with the
   credential lines above) — and export both in the operator shell:

   ```
   AOS_HOME=<sandbox>/aos-home
   AOS_PRINCIPAL_ID=dana@example.com
   ```

   The aos home is `--home`/`AOS_HOME`, else `~/aos` — named, never discovered — so on a
   machine that has a real household, any `kb` or `aos-cap` call without it resolves the
   *real* one. The identity is `--principal`/`AOS_PRINCIPAL_ID` (used per call, never
   saved), else `<home>/.aos/kb-principal.yml`, which only `kb init` (from `--principal`
   or this variable) and `kb config set principal.id=` write; with neither, a write verb
   fails naming that file. Pinning Dana keeps "who ran the e2e" out of a committed
   snapshot: it is not a property of the install.

   The `.env` does not reach everything. Hermes's desktop/dashboard backend ticks every
   profile's cron **without loading that profile's `.env`**, so a scheduled command carries
   `AOS_HOME` itself (kb-init's `sync` row — check the wrapper before its first tick) and
   agent jobs are paused right after the snapshot (step 5). Finish teardown before the
   earliest agent job's hour.
3. **Install** — tell the agent (`hermes -p aos-test -z "<prompt>"`, falling back to the
   default profile with the same prompt if the fresh profile has no credentials):

   > You are the Hermes harness agent installing from the aos kit. The aos household
   > is at `<sandbox>/aos-home` (not the default `~/aos`; this profile's `.env` sets
   > `AOS_HOME` to it): the kit clone is `aos-home/upstream`, the user's personal repo is
   > `aos-home/personal`. Read `upstream/BOOTSTRAP.md` and follow it exactly. The
   > interviews already ran — the overlay files (`MOD.md`, `capabilities/*/MOD.md`) are
   > present in `personal/` at mirrored paths, and the base registry is at
   > `aos-home/.aos/kb-registry.yaml`. Your install home (the "front agent") is the
   > `aos-test` profile (`~/.hermes/profiles/aos-test`); create each capability agent as
   > the profile `aos-<agent id>` (`aos-archiver`, `aos-steward`). Profiles outside
   > `aos-*` belong to another household on this machine: never adopt, modify or count
   > them — their cron jobs are not this household's schedules. Renders land in
   > `personal/` and skills are symlinked per the contract. Install: kb (work-tracker
   > comes later, as its own prompt — see the Day-N step). The lockfile lives at
   > `aos-home/.aos/installs.lock.yaml` (`aos-cap --home <sandbox>/aos-home`).

   The installer gets **no other context** — BOOTSTRAP + the capability-lifecycle
   contract + capability + cheat-sheet + overlay must suffice; that is the test.
   Bootstrap installs capability-lifecycle (ten skills — the interview engine among
   them, so there is no separate onboarding install) and kb. The name gate
   (`aos-cap skills … --check`) runs before each install; a fresh `aos-test` profile has
   no skills of its own, so it must come back clean.

   **Day-N step** (the seam this exists to prove): a SEPARATE, fresh prompt with no
   bootstrap context — `hermes -p aos-test -z "install work-tracker from the aos household
   at <sandbox>/aos-home. Agents go in aos-<agent id> profiles; profiles outside aos-* are
   another household's — never adopt, modify or count them."` (default-profile fallback
   as above) — must trigger the materialized `capability-install` skill and complete the
   install. The second sentence is harness namespace, not install context (see Namespace).

4. **Check**: `uv run --project tools/aos_lint python -m aos_lint.golden.check --live` runs the structural checks against the
   materialized tree (expectations in `tests/golden/expectations/*.yaml`), plus the
   canary check against the pre-state snapshot.
5. **Snapshot**: `uv run --project tools/aos_lint python -m aos_lint.golden.normalize <paths>` → commit under
   `tests/golden/hermes/<cap>/`. The commit diff is the reviewable render (RFC-002).
   Save the run transcript to `tests/transcripts/`.

   **Then pause every `aos:*` job** (`hermes -p <profile> cron pause <id>`) — after the
   snapshot, so the snapshot records the jobs as installed. The backend that would tick them
   does not load the profile `.env` (step 2), so a job that fired would act on `~/aos`.
   Re-check after the evolve step: it edits a job, and an edit must not leave it enabled.

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
   "change work-tracker's steward hour to 22:00", plus the Day-N step's namespace sentence
   (a real `wt-steward` profile carries a job of the very same name) — must route through
   `capability-evolve`: the cron job changes, the change lands in
   `personal/capabilities/work-tracker/MOD.md` (auto-committed by the persist hook), and
   `aos-cap verify` stays clean. **Note when running via the default-profile fallback:**
   the fallback agent does not carry the materialized skills in context, so the prompt
   must name the skill path explicitly (`~/.hermes/profiles/aos-test/skills/
   capability-evolve/SKILL.md`) — otherwise it edits the cron
   natively and skips the ledger, which is a fallback artifact, not a skill failure.
   Capture mode is then the second half of the test: fold the existing change into the
   ledger and confirm the persist commit.
6. **Remove**: tell the agent to remove per the cheat-sheet Removal section (with the
   Day-N step's namespace sentence); verify with `prestate.sh` that `~/.hermes` matches
   pre-state; `hermes profile delete` the test profiles.

   **The tools are machine-wide, not per-household.** Where a real household already has
   `aos-kb`/`aos-cap` installed, the install's `uv tool install --from <sandbox>/…`
   repoints them at the sandbox clone and removal's `uv tool uninstall` deletes them from
   under it. Back up `~/.local/share/uv/tools/aos-{kb,cap}` before step 3 and restore them
   (with their `~/.local/bin` links) right after this step.

## Judging (agentic, advisory)

For re-renders, a fresh judge subagent gets old + new snapshots, the capability, the
fixture MOD, and `RUBRIC.md`, and returns `EQUIVALENT | DIVERGENT` per criterion. The
structural checks are the blocking floor; the judge informs the human review.
