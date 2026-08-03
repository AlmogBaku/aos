# Full e2e — all three capabilities, real Hermes (2026-08-01)

`golden: 0 failures`. Hermes v0.19.0, bedrock/claude-sonnet-5, disposable `aos-test` /
`aos-archiver` / `aos-steward` profiles, household at `tests/.sandbox/aos-home`.
**Canary clean** before and after — the user's own profiles, root skills and 19 cron jobs
untouched.

## The blocker, root-caused

Three earlier Day-N attempts stalled with **zero output**, and I wrongly called it a
provider outage. It was not. `ps` showed `futex_do_wait` with 0s CPU — blocked on a lock,
not the network — and the lock was `auth.lock`: a freshly-created profile writes its own
`.env`, which SHADOWS the root's, and the root's is where `AWS_PROFILE`/`AWS_REGION` live.
Hermes then blocks forever resolving credentials it cannot see. The first install of the
day worked only because the profile had not yet been given an `.env`.

Fix: copy `AWS_PROFILE`, `AWS_REGION`, `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE` into the
profile `.env`. **PROTOCOL.md step 2 says to copy `config.yaml` but not the credential
env** — that is the gap, and it is now recorded there.

## Verified in this run

- three capabilities recorded at current versions: `capability-lifecycle 0.3.6`,
  `kb 0.7.3`, `work-tracker 0.1.2`; `aos-cap verify` → **clean: 3 entries verified**
- **the Day-N seam**: a fresh prompt with no bootstrap context ("install work-tracker from
  the aos household at …") triggered the *installed* `capability-install` skill and
  completed the install — renders, links, the `aos-steward` profile, and the
  `aos:work-tracker:nightly-steward` schedule
- **zero unresolved `{{skill:}}`/`{{agent:}}` slots** in any rendered file; `naming.md`'s
  escaped examples survived as literals
- both context blocks at `@0.3.6` (`mode-boundary` + `concepts`), `<home>` baked
- computed agent names (`aos-archiver`, `aos-steward`) and exact `used_by` scoping —
  `wt-steward` links into the steward only, never the front agent
- `{{mod: action_format}}` → `verb-first` from the fixture MOD

## Two stale sentinels retired

`{text: "choir"}` and `{text: "19:00"}` asserted the global MOD's sacred time was distilled
into the steward's files. Commit `74f32fd` deliberately stopped doing that — the harness owns
user context — and the steward's own spec says "It reads the global overlay and honours it",
i.e. it reads `MOD.md` at runtime rather than carrying a copy. The sentinels contradicted the
contract; this run is simply the first to exercise the steward and expose it. **The
expectation was the stale side, not the render.**

## Run log

work-tracker is fully installed and verified. Summary:

**Installed work-tracker 0.1.2** into the aos-test Hermes profile, from the household at `<repo>/tests/.sandbox/aos-home`.

What landed:

- **The `commitments` base** — a new private kb base at `tests/.sandbox/kb/commitments`, registered in `personal/kb-registry.yaml`. All four load-bearing base changes applied as `user`-attributed commits: the `actions` zone declared (`kind: wiki`), the `action` type added, the eight bookkeeping frontmatter extensions declared (`due estimate block slipped since waiting_on status project`), and both grant rows added (`agent:main` on `actions/** index.md`, `agent:steward` on `actions/** projects/** index.md`). Copied the `actions/AGENTS.md` zone contract from the shipped template. `kb lint` on the base now reports 0 criticals (only the pre-existing "weak principal" finding, unrelated to this install).
- **Five skills rendered and symlinked**: `work-tracker` (entry, → main + steward), `wt-capture`, `wt-schedule`, `wt-update` (→ main), `wt-steward` (→ steward). All `{{mod:}}` slots resolved against the existing `MOD.md` answers (steward hour 22:47, verb-first phrasing, 14-day followup cadence, 90-day retention).
- **The `aos-steward` profile** — new Hermes profile, same model config as the front agent, toolset trimmed to terminal/file/skills/todo/session_search/cronjob (no messaging, matching the steward's "never act outward" contract). `SOUL.md` written from the agent's purpose text.
- **One cron job**: `aos:work-tracker:nightly-steward` at `47 22 * * *` on `aos-steward`, running the `wt-steward` skill — the user's chosen hour, not the 23:00 default.
- **Lockfile**: recorded and `aos-cap verify work-tracker` is clean (6 artifacts, 6 links, 1 schedule).

Degraded mode in effect: no calendar skill is installed on this harness, so `calendar.write` runs degraded — commitments, statuses and the steward pass all work, but `wt-schedule` will say so rather than silently placing blocks; the steward's `--without block` backstop catches anything left unscheduled.

One thing worth flagging: the kb-principal identity in this sandbox is a synthesized `<user>@<host>.local` rather than a real one — that's a kb-level onboarding gap predating this install, not something work-tracker introduced, and it's the one remaining lint finding.
