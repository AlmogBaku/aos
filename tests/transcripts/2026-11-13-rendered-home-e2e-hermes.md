# Full e2e — renders leave `personal/` for `rendered/` (capability-lifecycle 0.7.0) (2026-11-13)

`golden: 0 failures`, live and snapshot. Hermes v0.23.1 (2026.9.24), bedrock /
claude-opus-5-5, disposable `aos-test` / `aos-archiver` / `aos-steward` profiles, household at
`tests/.sandbox/aos-home`, upstream cloned from branch `almogbaku/rendered-home` (`b161746`,
working tree clean). The run re-records the golden snapshot for **capability-lifecycle 0.7.0 /
kb 0.8.3 / work-tracker 0.1.5**: every render lives at `<aos_home>/rendered/<id>/`, written only
to `rendered/.staging/<id>/` and put live by `aos-cap swap <id>`.

`aos-test` was the operator's own working profile on this machine. With the operator's explicit
go-ahead it was backed up outside the repo, then deleted at the start of step 1, before the
pre-state was written. Restoring it is the operator's step and is not part of this run.
`aos-archiver` and `aos-steward` did not exist.

Times are machine-local (UTC+2). The fixture's hours are Europe/Lisbon (UTC+0).

## Timeline

| step | prompt / command | start → end | exit |
|---|---|---|---|
| 1 free `aos-test` | `hermes profile delete aos-test -y` (backup checked first: the directory copy has the same 1947 names as the live profile) | 19:28:51 | 0 |
| 1 prestate | `prestate.sh` → `tests/.sandbox/prestate.txt`, plus a wider fingerprint (below) | 19:29 | 0 |
| 1 seed | upstream `git clone --branch almogbaku/rendered-home`; `personal/` `git init`, fixture overlay copied, `diff_review: auto-accept`, identity Dana Fixture, one seed commit; `.aos/kb-registry.yaml` from the fixture | 19:31 | 0 |
| 2 profile | `hermes profile create --no-alias aos-test`; `config set` `model.provider`, `model.default`, `platform_toolsets.cli` `[terminal, file, skills, cronjob]`, `terminal.shell_init_files` + `<sandbox>/path.sh`; `.env` gets `AWS_PROFILE`/`AWS_REGION` and the five pins | 19:31:11 | 0 |
| 2 smoke | `hermes -p aos-test -z "Reply with exactly: READY"` | 19:32:07 (7 s) | 0, `READY` |
| 2 smoke pins | print `AOS_HOME`, `AOS_PRINCIPAL_ID`, `UV_TOOL_DIR`, `UV_TOOL_BIN_DIR`, first PATH entry | 19:32:18 | 0, first entry `<sandbox>/uv/bin` |
| 3 bootstrap | PROTOCOL step-3 prompt, verbatim | 19:33:32 → 19:38:21 | 0 |
| 3 Day-N | `install work-tracker from the aos household at <sandbox>/aos-home.` + namespace sentence | 19:39:24 → 19:44:05 | 0 |
| 4 check | `aos_lint.golden.check --live` · `prestate.sh` diff · `aos-cap --home <sandbox>/aos-home verify` | 19:44:34 | 0 (`golden: 0 failures`) · identical · `clean: 3 entries verified` |
| 5 snapshot | `aos_lint.golden.normalize` × 4 roots into an emptied `full-install/`; 9 Hermes runtime files dropped (finding 1) | 20:24:01 | 0 |
| 5 pause | `hermes -p <profile> cron pause` × 4 `aos:*` jobs | 20:24:13 | 0 |
| 5 snapshot check | `aos_lint.golden.check` (snapshot mode) · `gates.privacy tests/golden/hermes/full-install` | — | 0 (`golden: 0 failures`) · clean |
| 5 evolve | `change work-tracker's steward hour to 22:00.` + namespace sentence | 20:24:37 → 20:25:23 | 0 |
| 5 capture | `Run capture mode for work-tracker: fold the existing steward-hour change into the ledger and confirm the persist commit.` + namespace sentence | 20:26:23 → 20:27:08 | 0, nothing to fold |
| 5 capture (added) | operator hand-edit to the live `wt-capture` render, then `I hand-edited work-tracker's wt-capture skill. Capture my edit so it survives upgrades.` + namespace sentence | 20:27:36 → 20:28:16 | 0 |
| 5 re-check | every `aos:*` job still `enabled: false`, `state: paused` | 20:28:33 | — |
| 6 remove | removal prompt (below) + namespace sentence | 20:28:45 → 20:30:43 | 0; `installs: {}` |
| 6 canary | `prestate.sh` diff · fingerprint diff | 20:31 | identical · identical |
| teardown | `hermes profile delete aos-test -y` · `prestate.sh` diff · fingerprint diff | 20:31:06 | 0 · identical · identical |

The namespace sentence: *"Agents go in aos-<agent id> profiles; profiles outside aos-* are
another household's — never adopt, modify or count them."*

The removal prompt: *"remove every capability installed from the aos household at
`<sandbox>/aos-home` — work-tracker, kb and capability-lifecycle — per capability-remove and the
Hermes cheat-sheet's Removal section."* + the namespace sentence.

### How the run was held in the sandbox

- **Prompts ran from an empty directory outside any git repo.** Hermes's `-z` loads the
  `AGENTS.md` chain from the git root down to the cwd. Run from inside the upstream clone, it
  would have handed the installer the kit's contributor guide, which is context the test
  forbids.
- **Agent profiles were pinned within 5 s of creation.** A watcher appended the two credential
  lines and the five pins to each new `aos-*` profile's `.env`, under the same flock Hermes's
  `.env` writer takes, and set `terminal.shell_init_files`. `aos-archiver` was created at
  19:36:40 and pinned at 19:36:45; `aos-steward` at 19:42:07 and 19:42:11. Neither install
  recorded a pin as its own: `env_lines` is `[AOS_AGENT]` and `config_keys` is
  `platform_toolsets.{cli,cron}` for both. The Day-N agent noticed the pins arrive and dropped
  its own duplicate lines.
- **A wider fingerprint, beyond `prestate.sh`.** It covered the real household's `.aos/` files
  and `personal/` HEAD, the machine's `aos-cap`/`aos-kb`/`aos-session` uv tools (receipt and
  RECORD hashes) and their `~/.local/bin` links, `~/.hermes/scripts/`, and every non-`aos-*`
  profile's `config.yaml`, `.env`, `SOUL.md`, skill links and cron jobs (hashes only). It was
  identical before the bootstrap, after it, during evolve, after removal, and after teardown.
- **The sync job acted only on the sandbox.** `aos:kb:sync` ticked nine times (19:41 → 20:21)
  before the pause, all `ok` and silent. Its wrapper exports `AOS_HOME=<sandbox>/aos-home` and
  `PATH=<sandbox>/uv/bin:$PATH` itself. Neither of those reaches the backend that ticks it
  otherwise.

## What this run proves (capability-lifecycle 0.7.0)

- **Renders live in `rendered/`, none in `personal/`.**
  - `rendered/capability-lifecycle/skills/` holds the ten lifecycle skills,
    `rendered/kb/skills/` the seven kb skills, and `rendered/work-tracker/skills/` the five
    work-tracker skills.
  - `personal/` holds exactly `MOD.md`, `capabilities/kb/MOD.md` and
    `capabilities/work-tracker/MOD.md`. No `personal/capabilities/*/skills/` exists.
  - Bootstrap and Day-N made no `personal/` commit, because neither changed an answer. The
    only commits after the seed are evolve's and capture's.
- **Every harness link points into `rendered/`.**
  - The links are `aos-test` 21, `aos-archiver` 1 and `aos-steward` 2, plus `aos-test`'s
    `skill-creator` into `vendor/`.
  - No copy exists: no non-link, non-bundled skill dir is in any `aos-*` profile.
  - `expect_links` passes live.
- **Every lockfile link target is under `rendered/`.**
  - capability-lifecycle 0.7.0 has 38 artifacts and 11 links (10 into `rendered/`, 1 into
    `vendor/`).
  - kb 0.8.3 has 22 artifacts and 8 links.
  - work-tracker 0.1.5 has 7 artifacts and 6 links.
  - No artifact path is under `personal/`. `.aos/harness.yml`'s `sheet` is
    `<aos_home>/rendered/capability-lifecycle/skills/capability-lifecycle/reference/harness-hermes.md`.
- **The installer staged, gated and swapped.**
  - Each install ran `aos-cap render <cap-dir> <skill> --out
    $AOS_HOME/rendered/.staging/<id>/skills`, then a diff gate.
  - It then ran `aos-cap --home $AOS_HOME swap <id>` before creating any link: capability-lifecycle
    at 19:34:17, kb at 19:36:38, work-tracker at 19:42:03.
  - Nothing was declined, so no `discard` ran.
  - `rendered/.staging/` was empty after every step and at the end. `swap` leaves an empty
    `rendered/.replaced/`.
- **Day-N works with no bootstrap context.** The fresh prompt loaded the materialized
  `capability-install` skill (`skill_view`) and ran the name gate over `aos-test` and
  `aos-archiver`. It then staged, swapped, created `aos-steward`, and set
  `aos:work-tracker:nightly-steward` at `47 22 * * *` Europe/Lisbon.
- **Evolve edits the job and the answer.**
  - The prompt routed through `capability-evolve`.
  - `steward_hour` changed from 22:47 to 22:00 in `personal/capabilities/work-tracker/MOD.md`
    (`da7de19`, authored by Dana Fixture).
  - The job changed to `0 22 * * *` and stayed paused, `rehash` ran, and `verify` reported
    `clean: 3 entries verified`.
  - No render mentions the hour, so nothing was staged.
- **Capture mode records a hand-edit to an unversioned render.**
  - The PROTOCOL's capture prompt had nothing to fold: evolve had already written the answer.
    The agent confirmed `da7de19` and that `personal/` was clean, and re-ran `rehash`/`verify`.
  - To test the fold itself, the operator appended one synthetic paragraph to the live
    `rendered/work-tracker/skills/wt-capture/SKILL.md`. It said choir commitments get
    `tags: [choir]`. `verify` then reported `work-tracker: DRIFT …/wt-capture/SKILL.md`.
  - The capture prompt routed through `capability-evolve` and read `reference/overlay.md`. To
    compare, the agent rendered a fresh `wt-capture` into `$TMPDIR`, outside the household, so
    `.staging/` stayed empty.
  - It found that paragraph was the only part the MOD did not explain. It added the paragraph
    under "Capture preferences" with a `patch` and re-applied nothing.
  - It then ran `rehash` (`verify` clean) and committed `5e40246` as Dana Fixture.
  - Under 0.7.0 this write is the only record of the edit, because `rendered/` is not a repo.
- **Removal sends renders to the OS trash.**
  - The order was work-tracker → kb → capability-lifecycle, ending with `installs: {}`.
  - Every link was removed, the four jobs deleted, the marker blocks stripped and the config
    keys unset. `aos-archiver` and `aos-steward` were deleted, each after its recorded
    `SOUL.md` hash matched.
  - `kb` and `aos-cap` were uninstalled from `<sandbox>/uv`, leaving an empty `bin/`.
  - Each `rendered/<id>/` went to `~/.local/share/Trash` (three entries), not `rm -rf`.
    `personal/` was untouched. The MOD files, `.aos/kb-principal.yml`, `.aos/kb-registry.yaml`
    and `vendor/anthropic-skills` were kept, and the agent offered to trash them.

## Canary

`prestate.sh` (root `config.yaml` sha256, the non-`aos-*` profile list, the root `skills/`
listing hash, the 19 root cron job ids) was byte-identical to `tests/.sandbox/prestate.txt` at
every comparison:

- after the bootstrap;
- at step 4;
- after removal;
- after the test `aos-test` was deleted.

The wider fingerprint above was identical at the same points. The machine's own `aos-cap` 0.6.2,
`aos-kb` 0.8.2 and `aos-session` 0.1.3 were never reinstalled or uninstalled: their receipts and
RECORDs were unchanged, and so were their `~/.local/bin` links.

## Findings

1. **The normalizer does not know Hermes 0.23's runtime files.** Normalizing the four live roots
   produced 152 files. Nine of them are harness runtime state, not install artifacts:
   - `{front,archiver,steward}/gateway.lock`
   - `{front,archiver,steward}/runtime/bot_live_delivery/.lock`
   - `front/runtime/active_sessions.json`
   - `front/runtime/active_sessions.lock`
   - `front/context_length_cache.yaml.lock`

   `.lock` is outside `TEXT`, so `gateway.lock` is byte-copied un-normalized. It is JSON holding
   the gateway's pid, argv, start time and the absolute `hermes_home`, which would fail
   `gates.privacy` and churn on every run. The nine files were deleted from the normalized
   output, and nothing else in it was touched. The committed snapshot is the normalizer's output
   minus exactly those paths, so `check_normalization_is_idempotent` holds. **Owed, not fixed
   here:** the normalizer's `SKIP` (or `SKIP_FILE`) needs `gateway.lock`, the `runtime/`
   directory and `context_length_cache.yaml.lock`. That is a `tools/` change.
2. **Hermes 0.23 stamps `origin` on jobs created from the CLI.** All four `aos:*` jobs carry
   `origin: {platform: local, chat_id: local-<hash>, user_id: "uid:<uid>"}`, where the 2026-10-21
   snapshot had `origin: null`. The agents created them with `hermes -p <profile> cron create`
   from inside their own terminal, which the cheat-sheet's `mapping.cron` prescribes. The
   cheat-sheet's "never write an `origin:` field" was kept by the agent; Hermes wrote the field.
   The normalizer's `_scrub` does not touch `origin`, so `archiver/cron/jobs.json` and
   `steward/cron/jobs.json` carry the machine's numeric uid. `gates.privacy` checks paths only
   and passes. **Owed:** scrub `origin.user_id`, or the whole `origin`, in `_scrub`. Re-running
   the normalizer over the committed snapshot then fixes it with no live run.
3. **The `wt-capture` render contradicts itself.** The 2026-10-21 render resolved the fixture's
   "single 🦜 — nothing else, ever" by dropping the two-minute-job question. This render keeps
   the source row verbatim: `trivial` → say *"that's a two-minute job — worth doing now?"*, and
   "ask about the two-minute job in the same breath as confirming". It also rewrites the
   confirmation as "the 🦜 alone". This is agent-decided render variance that the structural
   checks cannot see, so it is a question for the judge (`RUBRIC.md`).
4. **The steward's job prompt is the source `prompt_ref` verbatim.** The 2026-10-21 install
   added a `(household: AOS_HOME=…)` note and a `[SILENT]` delivery paragraph. This one adds
   neither, and the job delivers to the fixture's `whatsapp:+000000000000`. The kb jobs'
   prompts do carry the household, through an agent-written preamble. The job was paused before
   its hour, as PROTOCOL step 5 requires.
5. **Evolve and capture: the agent committed the MOD changes itself** (`da7de19`, `5e40246`),
   by running `git add`/`git commit` in its terminal. No persist hook ran. Step 5 expects the hook
   to make that commit, as the 2026-10-12 runs also found (findings 6 there).
6. **A paused job keeps its old `next_run_at` after an edit.** After the edit to `0 22 * * *`,
   `next_run_at` still read 22:47. Both evolve and capture flagged this and left the job paused,
   as in the 2026-10-12 runs.
7. **Smaller observations.**
   - The bootstrap agent noted that `aos-cap agents --check` gates the computed name
     `kb-archiver`, not the `aos-archiver` the prompt names, so the gate never sees the profile
     that actually exists. That is a seam of the test namespace.
   - The fixture kb MOD carries no `principal_id` or `curation` answer. The agent used
     `dana@example.com` from the prompt and the default `self`, and did not write either into
     MOD, which the 2026-10-12 run did.
   - `hermes profile delete` writes a tombstone at `profiles/.deleted/<name>`, and a directory
     restore must clear it (2026-10-12, finding 8). The teardown left a fresh one for `aos-test`.
     The ones for `aos-archiver`/`aos-steward` from 2026-10-21 were cleared by this run's
     `profile create` and re-written by its removal.

## Deviations from the protocol

- **`aos-test` was not this kit's leftover.** Step 1's stop rule was overridden by the
  operator's explicit authorization. The profile was deleted at the start of step 1, from a
  verified backup, and the operator restores it.
- **`--no-alias`** on `hermes profile create`, as on 2026-10-21, so no wrapper script landed in
  `~/.local/bin`.
- **Only `AWS_PROFILE`/`AWS_REGION` were copied** into each profile's `.env`. The root `.env`
  carries no `SSL_CERT_FILE`/`REQUESTS_CA_BUNDLE` lines, and the smoke test passed without them.
- **Nine runtime files were dropped from the normalized snapshot** (finding 1).
- **One capture step was added** (the hand-edit), because the PROTOCOL's capture prompt had
  nothing to fold once evolve had written the answer.

## Teardown

- Removal left `installs: {}`, deleted both agent profiles, emptied `<sandbox>/uv`, and moved
  three renders to the trash. `personal/` is unchanged by removal: three commits, seed +
  evolve + capture.
- The test `aos-test` was deleted. No `aos-*` profile exists. The watcher stopped at 20:31:12.
- `tests/.sandbox/` is left in place.

## Snapshot

143 files (`front/`, `archiver/`, `steward/`, `home/`), all from this live run, normalized by
`aos_lint.golden.normalize`. Nothing came in by `aos-cap render`. The old snapshot was removed
first, so nothing of the old layout survives:

- **62 moved:** every render file went from `home/personal/capabilities/*/skills/` to
  `home/rendered/*/skills/` (36 capability-lifecycle, 20 kb, 6 work-tracker).
- **42 changed:**
  - origin stamps and SOUL marker blocks 0.6.0/0.8.1/0.1.4 → 0.7.0/0.8.3/0.1.5;
  - this branch's prose;
  - `harness.yml`'s sheet path and every lockfile path, now under `rendered/`;
  - the concepts block naming `rendered/`;
  - the jobs' `origin` and `timezone` fields (finding 2);
  - the agent-decided renders and SOULs (findings 3–4).

## Agent reports, verbatim

The only edits are [the redaction pass](README.md): one private profile name became `[…]`.

### Bootstrap install

Welcome to aos, Dana. It adds capabilities to the Hermes setup you already run. Your interview answers are stored in your own private repo (personal/MOD.md), and nothing goes live without a diff. Because your root MOD.md sets diff_review: auto-accept, each diff was shown and accepted automatically. The lifecycle layer and kb are installed and running: aos-cap verify reports both lockfile entries clean.

Installed:

1. capability-lifecycle 0.7.0, on the front agent (aos-test)
   - The aos-cap tool, installed into the sandbox uv dir. The lockfile is at aos-home/.aos/installs.lock.yaml, and the harness is recorded as hermes.
   - Ten skills, rendered to aos-home/rendered/capability-lifecycle/ and symlinked into ~/.hermes/profiles/aos-test/skills/: capability-lifecycle, -install, -upgrade, -remove, -onboard, -import, -build, -contribute, -evolve, -review.
   - Two marker blocks added to aos-test's SOUL.md: mode-boundary and concepts.
   - skill-creator: cloned to aos-home/vendor/anthropic-skills (commit 2c5958e) and symlinked, not copied.
   - The global interview had already run, so I used your existing personal/MOD.md unchanged.

2. kb 0.8.3
   - The kb tool, installed into the sandbox uv dir.
   - Seven skills on aos-test: kb, kb-capture, kb-route, kb-recall, kb-init, kb-adopt, kb-import. kb-route includes your routing rule: Acme, client and ticket items go to acme-kb only by rule or explicit tag, never by guess. Choir and family items always go to personal-kb.
   - A new profile, aos-archiver. Its SOUL.md is the archiver's purpose statement. It can only use terminal, file and skills tools (no messaging, in both CLI and cron), and it's hidden from the bots list. It has the kb skill linked and AOS_AGENT=agent:archiver in its .env.
   - Two bases, created with kb init (the first one with --principal dana@example.com):
     - personal-kb: private, the default base
     - acme-kb: shared, curation self
     Both live under tests/.sandbox/kb/. Both start with the archiver's write rules (grant rows) for all five areas it maintains, and kb lint reports 0 critical issues and 0 findings on each.
   - The kb tool also wrote two machine-local files I didn't record in the lockfile: .aos/kb-principal.yml (dana@example.com for all bases) and an update to .aos/kb-registry.yaml. Your routing channels and keywords in the registry are kept.

Cron jobs, all on aos-archiver and all delivering locally:
   - aos:kb:nightly-promote, 23:30 daily, Europe/Lisbon (bc0039f434ca)
   - aos:kb:weekly-maintain, Saturday 07:00, Europe/Lisbon (21b2f24003f4)
   - aos:kb:sync, every 5 minutes (4cc517ff2d7d). It runs scripts/aos-kb-sync.sh with no model, and stays silent unless the sync fails.

No degraded modes are in effect: cron is available, so every job is real.

Things you should know:
   - Agent name: aos-cap computes the archiver's name as kb-archiver. I created it as aos-archiver because you asked for that profile naming, which overrides the contract's never-rename rule. This means aos-cap's name check covers "kb-archiver", not the profile that actually exists.
   - Sync setting: you answered "manual" in the interview, but the registry you seeded already said sync: none for both bases, and kb init kept that. Either way nothing pushes, since neither base has a remote.
   - Missing answers: your kb MOD.md has no principal_id or curation answer. I used dana@example.com as you told me and curation self, the default. I didn't edit MOD.md.
   - Nothing else changed: the root ~/.hermes config is byte-identical to its recorded starting state, I didn't touch or count any profile outside aos-*, and both upstream/ and personal/ have no uncommitted changes.
   - Not done: I didn't create a private remote for personal/ or fork upstream. I can offer either whenever you want.

Next step: work-tracker is a separate install. Its overlay is already in personal/capabilities/work-tracker/MOD.md, and its agent will become the aos-steward profile.

### Day-N install

work-tracker 0.1.5 is installed and `aos-cap verify` comes back clean. Your existing MOD.md answers were used, so there was no interview. Your root MOD.md is set to auto-accept, so I showed the diff and went ahead without waiting for approval.

What's set up:

- **Front agent (aos-test):** four skills, all linked to the live render.
  - work-tracker: answers "what's overdue / what am I waiting on".
  - wt-capture: files a commitment the moment you make it.
  - wt-schedule: finds time and blocks it.
  - wt-update: handles "done", "still waiting on…" and "forget it".
- **Steward agent (new profile aos-steward):**
  - It has the work-tracker and wt-steward skills, plus its own SOUL.md, and it is hidden from the Desktop bots roster.
  - It can use only the terminal, file and skills toolsets.
  - It acts as agent:steward, set through AOS_AGENT in its .env.
- **Cron job `aos:work-tracker:nightly-steward`:** runs at 22:47 Europe/Lisbon every night (your steward_hour; the default is 23:00) and delivers to whatsapp:+000000000000.
- **New private base `commitments`** at `~/aos/upstream/tests/.sandbox/kb/commitments`. In one commit I added:
  - an `actions/` zone
  - the `action` type
  - the 8 frontmatter extensions
  - grant rows for agent:main and agent:steward
  - the actions/AGENTS.md zone contract

  `kb lint` on it is clean.

Your preferences in the render:
- Capture confirms with a single 🦜 and nothing else.
- Titles are verb-first, with the deadline in the title.
- Estimates use 30-minute steps.
- Blocks go on your personal calendar, within working hours, never during choir practice (Thursdays 19:00–21:00).
- The steward chases waiting items after 14 days, flags someday items as cold after 90 days and questions anything that has slipped 3 times.
- Completed items expire after 90 days.

Choices I made that you might want to reverse:
- **Confirmations:** your "🦜, nothing else, ever" conflicts with the shipped behaviour of saying whether a block was taken. I followed your rule. When you capture something, you won't be told whether time was found. Commitments with no block show up in the steward's nightly backstop count. You only hear about missing time when you ask for time directly.
- **working_windows:** you never answered this optional question. Scheduling uses your global working hours plus the Thursday choir rule.
- **`.env` duplicates:** Hermes seeded the steward's `.env` with the sandbox pins while I was adding them myself. I removed my duplicate lines; only AOS_AGENT is recorded as added by this install.

Two things you still need to set up:
1. **WhatsApp:** it isn't paired to aos-steward or bound to aos-test. Until it is, the nightly report has nowhere to go and messages you send on WhatsApp won't reach the front agent. The binding needs profile_routes and `gateway.multiplex_profiles` set. I didn't touch the gateway config because it's outside the aos-* profiles.
2. **Calendar:** no calendar skill is set up yet; google-workspace is installed but not configured. Until it is, wt-schedule records estimates but blocks no time.

Other notes:
- kb added the commitments base to `.aos/kb-registry.yaml` itself. That file is machine-local and isn't part of the install record.
- Only the aos-* profiles were read or changed.

### Evolve

The work-tracker nightly steward now runs at 22:00 Europe/Lisbon instead of 22:47. The change is saved in your MOD.md, so it survives every upgrade.

- **Your settings:** in `personal/capabilities/work-tracker/MOD.md` I changed the onboarding answer `steward_hour` from "22:47" to "22:00", and committed it to `personal/` (da7de19).
- **The scheduled job:** I changed job `aos:work-tracker:nightly-steward` (09ce46b53932) in the `aos-steward` profile to `0 22 * * *` using the hermes CLI. No other skill files mention the hour, so none needed editing.
- **Bookkeeping:** I refreshed the stored file fingerprints, and `aos-cap verify work-tracker` reports clean.

Two things to know:
- The job was already paused, and I left it paused. Because it's paused, Hermes still lists the next run as 22:47. I expect it to show 22:00 once you resume it, but I haven't checked that. Say if you want it resumed.
- I only touched `aos-steward`. Every profile not named `aos-*` was left alone.

### Capture (the PROTOCOL prompt)

Your 22:00 steward change is now in the ledger, and the commit that keeps it already exists.

- **Your MOD.md:** the onboarding answer in `personal/capabilities/work-tracker/MOD.md` already reads `steward_hour: "22:00"`. That's the right place for it, so I changed nothing there and there's no second, conflicting line. The shipped default is 23:00, so the entry stays.
- **The commit:** `da7de19` (2026-11-13 20:25 +0200), message "2026-11-13: work-tracker steward_hour 22:47 -> 22:00". `personal/` has no uncommitted changes, so no new commit was needed.
- **The lockfile:** I ran `aos-cap rehash work-tracker`, which refreshed all 7 artifact hashes. `aos-cap verify` then came back clean for all 3 installed capabilities.
- **The cron job:** `09ce46b53932` (aos:work-tracker:nightly-steward, profile aos-steward) is set to `0 22 * * *` Europe/Lisbon, which matches your MOD.md. The live skill files already carried the change, so there was nothing to re-apply.

Your 22:00 steward is recorded in your MOD.md and will survive every upgrade.

I only touched aos-* profiles. Profiles outside aos-* weren't read, changed or counted.

One problem: that cron job is paused. It was paused at 20:24, just before the hour change, and its stored "next run" still says the old 22:47 time. As it stands, the nightly steward won't run at all. I left it paused in case you did that on purpose. If not, `hermes -p aos-steward cron resume 09ce46b53932` will restart it and work out the next run from the new 22:00 schedule.

### Capture (the hand-edit)

I've saved your edit to your MOD.md, so it will survive every upgrade.

Your edit: anything that mentions the choir gets `tags: [choir]` in its page frontmatter. I compared your live wt-capture against a fresh render, and that paragraph was the only part your MOD didn't already explain. The 🦜-only confirmation and the verb-first titles with deadlines come from statements already in your MOD, so I didn't add those again.

What changed:
- `personal/capabilities/work-tracker/MOD.md`: added that rule under "Capture preferences". Your capture skill already has it, so I didn't re-render.
- `aos-cap rehash work-tracker`: recorded the new hashes, and `verify` now reports clean.
- Committed `personal/` as 5e40246.

Nothing outside the aos-* profiles was touched. The only profiles involved were aos-test and aos-steward.

### Removal

All three capabilities are removed and the lockfile is now empty (`installs: {}`). I did them in dependency order: work-tracker first, then kb, then capability-lifecycle. Only aos-* profiles were touched. wt-steward, […] and the default profile were not changed or counted.

What was removed:

work-tracker:
- Deleted cron job `aos:work-tracker:nightly-steward` (09ce46b53932).
- Unlinked 6 skills: 2 in aos-steward, 4 in aos-test.
- Sent its render to the trash.
- Unset its 2 `platform_toolsets` config keys.
- Deleted the aos-steward profile. Its recorded SOUL.md hash matched, which shows work-tracker created it, and nothing else used it.

kb:
- Deleted 3 cron jobs: nightly-promote, weekly-maintain and sync.
- Unlinked 8 skills.
- Sent its render to the trash.
- Unset its 2 config keys and removed `scripts/aos-kb-sync.sh`.
- Deleted the aos-archiver profile (same check as aos-steward) and uninstalled the `kb` tool.

capability-lifecycle:
- Unlinked 11 skills, including the `skill-creator` link into vendor/.
- Sent its render to the trash.
- Removed the 2 `aos:capability-lifecycle` marker blocks from aos-test's SOUL.md.
- Dropped its lockfile entry, then uninstalled `aos-cap`, since the lockfile entry had to go while the tool still existed.

Checked afterwards: no aos cron jobs remain, no skills are linked into the household, no aos markers are left in aos-test, and `rendered/` holds only empty `.staging` and `.replaced` folders. All three renders are in the OS trash, so you can restore them. Nothing was deleted with `rm -rf`.

The `AOS_AGENT` lines were in the two deleted profiles' `.env` files, so they were deleted along with those profiles rather than after asking you as a separate step.

Your answers survive: your MOD.md files (`personal/MOD.md`, `personal/capabilities/kb/MOD.md`, `personal/capabilities/work-tracker/MOD.md`) are untouched, and reinstalling brings each capability back with your settings.

Three things I left alone because they're yours to decide:
1. `.aos/kb-principal.yml`: the list of who authors writes on this machine.
2. `.aos/kb-registry.yaml`: the list of every knowledge base. A kb reinstall would quietly reuse both files, so delete them only if you want a fresh start.
3. `vendor/anthropic-skills`: the third-party clone behind skill-creator. Nothing links to it any more, so it can go if you want.

Should I send any of these to the trash?

The skills from this session stay in my context until you start a new session.

## Later the same day (2026-11-13), after this run

- The two normalizer findings above are fixed in the kit, not left owed. The normalizer now
  scrubs `uid:<digits>` to `uid:<UID>` (Hermes 0.23's cron `origin.user_id`). It also skips
  `gateway.lock`, `active_sessions.{json,lock}`, `context_length_cache.yaml.lock` and
  `runtime/bot_live_delivery/`. The committed snapshot was re-normalized for the uid only.
- One file did come in by `aos-cap render` after the run: the Hermes cheat-sheet (both
  snapshot copies). Its renders-migration skip list gained `.curator_backups`, which the
  read-only preview against a real household surfaced. That followed PROTOCOL's shortcut:
  an untouched skill (`capability-onboard`) first re-rendered byte-identical, then the sheet
  was rendered outside the household, normalized and copied in.
