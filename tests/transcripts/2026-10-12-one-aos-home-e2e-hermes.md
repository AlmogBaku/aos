# Full e2e — one aos home, real Hermes (2026-10-12)

`golden: 0 failures`, live and snapshot. Hermes v0.21.5 (2026.9.24), bedrock /
claude-opus-5-5, disposable `aos-test` / `aos-archiver` / `aos-steward` profiles, household at
`tests/.sandbox/aos-home`, upstream cloned from branch `one-aos-home` (`28dfbef`). The run
re-records the golden snapshot for **kb 0.8.0 / capability-lifecycle 0.5.0**: the aos home is
`--home`/`AOS_HOME`, else `~/aos`, with no cwd search; identity is `--principal`/
`AOS_PRINCIPAL_ID` (never saved), else `<home>/.aos/kb-principal.yml`; the registry moved
from `personal/` to `<home>/.aos/kb-registry.yaml`.

**Canary clean** before and after (`prestate.sh` byte-identical). Beyond it, a fingerprint of
everything the run must not change was identical at the end: the operator's real household
`.aos/` files, its `personal/` HEAD, the HEADs of the three real bases, `~/.hermes/scripts/`,
`~/.local/bin`, the `aos-kb`/`aos-cap` uv tools, and every non-`aos-*` profile's `SOUL.md`,
`config.yaml`, `.env`, skill links and cron jobs. A 10-second watcher logged no change to any
of them during the run, and no automatic pause was needed.

## Why this run is different: a real household on the same machine

Under the new contract, any `kb` or `aos-cap` call without `AOS_HOME` resolves the real `~/aos`.
So the protocol now pins it, and the run was built around that:

- `AOS_HOME=<sandbox>/aos-home` and `AOS_PRINCIPAL_ID=dana@example.com` in every profile's
  `.env` (operator-written: `aos-test` before the install, the two agent profiles within 10s
  of the install creating them, together with the credential lines) and in the operator shell.
  A smoke test confirmed both reach the terminal tool, and that subprocess `HOME` stays the
  real one, so nothing else would have caught a missing pin.
- The Hermes desktop/dashboard backend ticks every profile's cron **without loading the
  profile `.env`**. The sync wrapper had to carry `AOS_HOME` itself, and it did (below). Every
  `aos:*` job was paused right after the snapshot (18:27:49). The only job that ever fired was
  `aos:kb:sync` at 18:20, against the sandbox registry:
  `personal-kb: skipped (sync: none)`, `acme-kb: skipped (sync: none)`.
- The computed agent names (`kb-archiver`, `wt-steward`) can be real profiles here. A real
  `wt-steward` carries a job named exactly `aos:work-tracker:nightly-steward`, and the
  contract adopts a profile carrying an `aos:<capability>:` job. So both install prompts (and
  the evolve and removal prompts) now name the profiles and fence off everything outside
  `aos-*`. Every agent reported leaving `wt-steward` alone, and its job's fingerprint is
  unchanged.

## Timeline

| step | prompt / command | start → end | exit |
|---|---|---|---|
| smoke | `hermes -p aos-test -z` (print `AOS_HOME`, `AOS_PRINCIPAL_ID`, `HOME`) | 14s | 0 |
| 3 bootstrap | PROTOCOL step-3 prompt | 18:08:57 → 18:16:03 | 0 |
| 3 Day-N | `install work-tracker from the aos household at <sandbox>/aos-home.` + namespace sentence | 18:18:41 → 18:26:53 | 0 |
| 4 check | `aos_lint.golden.check --live full-install` | — | 0 (`golden: 0 failures`) |
| 4 canary | `prestate.sh` diff · `aos-cap --home <sandbox> verify` | — | identical · `clean: 3 entries verified` |
| 5 snapshot | `aos_lint.golden.normalize` × 4 roots | 18:27:34 | 0 |
| 5 pause | `hermes -p <profile> cron pause` × 4 jobs | 18:27:49 | 0 |
| 5 evolve | `change work-tracker's steward hour to 22:00` + namespace sentence | 18:28:28 → 18:32:24 | 0 |
| 6 remove | remove all three, per `capability-remove` + the Removal section | 18:32:48 → 18:38:36 | 0 |
| 6 canary | `prestate.sh` diff · lockfile | — | identical · `installs: {}` |

## Verified in this run

- three capabilities recorded at current versions: `capability-lifecycle 0.5.0` (38
  artifacts, 11 links), `kb 0.8.0` (22, 8), `work-tracker 0.1.2` (7, 6)
- **the Day-N seam**: a fresh prompt triggered the materialized `capability-install` and
  completed the install: renders, links, the `aos-steward` profile, the
  `aos:work-tracker:nightly-steward` job at `47 22 * * *`
- **the registry stayed machine state**: seeded at `.aos/kb-registry.yaml`, extended there
  by `kb init commitments`, and never copied into `personal/`
- **identity from the pin, never synthesized**: `kb init` wrote `.aos/kb-principal.yml`
  (`dana@example.com`, `*`) from `AOS_PRINCIPAL_ID`; every `personal/` commit is authored by
  Dana Fixture
- **the sync wrapper pins the household** (kb-init's `sync` row): `export AOS_AGENT=agent:archiver`,
  `export AOS_HOME=<sandbox>/aos-home`, `exec …/aos-kb/bin/kb sync --all`, with no
  `AOS_REGISTRY` and no `--registry`
- both context blocks on `aos-test/SOUL.md` at `@0.5.0`, `<home>` baked to the sandbox
- evolve: `steward_hour` 22:47 → 22:00 in `personal/capabilities/work-tracker/MOD.md`, the job
  edited to `0 22 * * *` and still paused, `aos-cap verify` clean
- removal walked each lockfile entry backwards; user data kept (MOD files, bases,
  `kb-principal.yml`, `kb-registry.yaml`), `kb-principal.yml` offered rather than assumed

## Findings

1. **Hermes 0.21 reads a job's `--script` only from the owning profile's `scripts/`.** It
   refuses paths outside it ("profiles never share files"). The installer put the wrapper in
   `aos-archiver/scripts/`, which is right for 0.21. The expectation looked in
   `root:scripts` (`~/.hermes/scripts/`, correct on 0.19), so it was the stale side and now
   checks `archiver:scripts`, which a snapshot can also testify to. **Owed, not fixed here:** the cheat-sheet's
   Materialization guide (item 6, "`--script` files → `~/.hermes/scripts/`") is stale for
   profile-owned jobs. Fixing it is a capability-lifecycle change (version bump plus re-render).
2. **The normalizer did not know Hermes 0.21's runtime files.** These include
   `backups/config/config.yaml.good.<ts>` (provider config copies, whose `.good.<ts>` suffix
   escapes the `config.yaml` rule), the cron ticker's stamps and `.fire-<hash>.lock`,
   `cron/output/<id>/` run logs, `plugin-update-checks/`, `models_dev_cache.etag`, and
   `state.db.<task>.lock`. `SKIP` was extended, with a parent-scoped rule for
   `cron/output` and a pattern for the hash- and task-named locks. Without this the snapshot
   would have carried private config and run-varying noise.
3. **The tools are machine-wide.** The install's `uv tool install --from <sandbox>/…`
   repointed the operator's real `aos-kb`/`aos-cap` at the sandbox clone (same code, same
   versions). Removal's `uv tool uninstall` then deleted them. Both had been backed up before
   step 3 and were restored at 18:40:29, receipts and RECORDs byte-identical. They were missing
   for at most ~4 minutes, and no real job in that window uses them. PROTOCOL step 6 now says so.
4. **No principal answer in the fixture kb MOD.** kb's interview asks for `principal_id`, and
   the fixture never answered it. The bootstrap agent filled it from `AOS_PRINCIPAL_ID`, said so
   in its report, and committed it as `onboard kb: principal_id`. That behavior is correct.
   The fixture could carry the answer instead.
5. **Day-N self-correction.** The first pass committed the base's config changes as
   `agent:main`, which the weekly grants audit would flag. The agent reset the fresh base and
   redid them as the user.
6. **Evolve: no persist commit.** "Nothing committed it automatically", so the agent committed
   the MOD change itself (`… steward_hour 22:47 -> 22:00`, authored by Dana Fixture). Step 5
   expects the persist hook to auto-commit.
7. **Timezone.** Both agent profiles got `timezone: Europe/Lisbon` from the global MOD
   (recorded as config keys), so `next_run_at` reads `+01:00`. Hermes left a paused job's
   `next_run_at` at 22:47 after the edit to `0 22 * * *`; the agent flagged this rather than
   resuming the job.
8. **Deleting or recreating a profile while the dashboard holds its `state.db`** leaves a
   retired WAL. Hermes then refuses that profile's session store, and the dashboard's session
   list failed for all profiles until the dashboard was restarted. The operator here never
   restarted it, and the teardown at 18:41 causes it again.

## Snapshot

142 files (`front/` `archiver/` `steward/` `home/`), all from this live run. Nothing was
re-rendered with `aos-cap render`. One deletion: `home/personal/kb-registry.yaml`. One
addition: `home/.aos/kb-registry.yaml`.

## Agent reports, verbatim

The only edits are [the redaction pass](README.md): operator paths became `~`, and one
private profile name became `[…]`.

### Bootstrap install

Dana's household is set up. The kit's lifecycle tooling and kb are both installed in this Hermes profile. Every artifact is recorded in the lockfile, `aos-cap verify` reports both entries clean, and both bases lint with 0 Critical and 0 Findings. Your root `MOD.md` says diff_review: auto-accept, so I took the gate as approved and didn't stop for confirmation.

What's installed:

1. capability-lifecycle 0.5.0 (the installer itself)
   - The `aos-cap` tool, plus a lockfile at `aos-home/.aos/installs.lock.yaml`.
   - Ten skills (`capability-install`, `-upgrade`, `-remove`, `-onboard`, `-import`, `-build`, `-contribute`, `-evolve`, `-review`, and `capability-lifecycle` itself). They're saved in `personal/capabilities/capability-lifecycle/skills/` and symlinked into `aos-test/skills/`.
   - `skill-creator`: Anthropic's repo is cloned into `aos-home/vendor/anthropic-skills` (at commit dbd4588) and symlinked in, not copied.
   - Two marked blocks added to the end of `aos-test/SOUL.md`. One makes the agent ask before setting up any new recurring job or automation; the other explains what aos and the household are. I didn't touch any other text in that file.
   - The global interview didn't need re-asking: `personal/MOD.md` already answers every question (Dana, Europe/Lisbon, working hours, choir on Thursdays, red lines, auto-accept).

2. kb 0.8.0
   - The `kb` tool (`aos-kb`), reinstalled from this household's copy of the kit.
   - Seven skills (`kb`, `kb-capture`, `kb-route`, `kb-recall`, `kb-init`, `kb-adopt`, `kb-import`), saved in `personal/capabilities/kb/skills/` with the household path filled in.
   - Two bases, created at the paths already in the registry:
     - `personal-kb`: private, and the default base. Its routing keywords (choir, family, home) and WhatsApp channel binding are kept.
     - `acme-kb`: shared, so it only accepts writes that are tagged explicitly or match a rule.
     - Each base's `AGENTS.md` lists the archiver's and front agent's write permissions.
   - A new archiver profile, `aos-archiver`:
     - Its identity file (`SOUL.md`) is written from the package's description of the role.
     - Its tools are cut down to file, terminal, skills and todo on both the CLI and cron, so it has no messaging tools.
     - It runs every kb write as the archiver (`AOS_AGENT=agent:archiver` in its `.env`), and its timezone is Europe/Lisbon.
     - It gets only the `kb` skill.
   - Three scheduled jobs, all owned by `aos-archiver`:
     - `aos:kb:nightly-promote` at 23:30 every night.
     - `aos:kb:weekly-maintain` at 07:00 on Saturdays.
     - `aos:kb:sync` every 5 minutes. It runs `scripts/aos-kb-sync.sh` with no model involved.
   - Your interview answers didn't include a kb identity, so I added `principal_id: dana@example.com` to `personal/capabilities/kb/MOD.md`. That address came from this profile's `.env`, not from you.
   - The `kb` tool also created two files on this machine that aren't tracked in the lockfile: `.aos/kb-registry.yaml` (updated) and `.aos/kb-principal.yml` (new).

Things to know:
- Nothing is actually synced yet. Your kb answers said manual sync and neither base has a remote. The registry still says `sync: none` from the pre-seeded file, and the sync job skips anything not set to automatic sync anyway. It will start working once a base gets a remote and is switched to automatic 5-minute sync.
- The `aos-archiver` profile has no API keys of its own and uses the keys from your shell environment, as Hermes warned when creating it.
- Every change in `personal/` is committed, in three dated commits. The `upstream/` kit is untouched and I made no remote writes. I only read the profiles outside `aos-*` to check for name clashes and didn't modify any of them.

Next, when you want it: "install work-tracker". That install will create the `aos-steward` profile.

### Day-N install

work-tracker 0.1.2 is installed, and `aos-cap verify` reports it clean. Your root MOD.md is set to auto-accept, so I applied the plan without stopping at the review step. kb and capability-lifecycle were already installed, so no dependencies needed adding.

What you have now:

- **Front agent (aos-test).** Four new skills: `work-tracker`, `wt-capture`, `wt-schedule` and `wt-update`. When you say "I need to…", it files the commitment and books time for it straight away.
- **New steward agent (aos-steward).** I created this profile fresh, with its own identity (`SOUL.md`), the `work-tracker` and `wt-steward` skills, and file/terminal/skills/todo tools only. Its kb edits are recorded under its own name (`agent:steward`). It uses the same model and timezone (Europe/Lisbon) as your other aos agents, and it answered a smoke test.
- **Nightly schedule.** `aos:work-tracker:nightly-steward` runs at 22:47 every night, which is your `steward_hour`. The first run is tonight.
- **New private base, `commitments`.** It's at `tests/.sandbox/kb/commitments` with `kb init`'s default template. All four required changes are in place:
  - the `actions/` zone is declared;
  - `action` is added to the page types;
  - the eight extra page fields are declared;
  - two permission rows are added, each tagged `via work-tracker@0.1.0`: the front agent can write `actions/**` and `index.md`, and the steward can also write `projects/**`.

  The `actions/` rules file (`actions/AGENTS.md`) is copied in. `kb lint` reports 0 criticals and 0 findings, and `kb grants check` confirms each agent's access is exactly as intended.
- **Your preferences, built into the skills.** The source files are untouched:
  - Confirmations are a single 🦜 and never repeat the commitment back.
  - Titles start with the verb and include any deadline.
  - Estimates are in 30-minute steps.
  - Time goes on your personal calendar only: nothing before 10:00, Friday afternoons for admin, at most 2 hours per sitting, and never during choir on Thursdays 19:00–21:00.
  - The steward nudges after 14 days, keeps finished items for 90 days, and asks you after 3 reschedules.

  The rendered skills are committed in `personal/` as 4045f25.

Two things that won't work fully until you set them up:

1. **WhatsApp.** Your reminder target is WhatsApp, but none of these profiles has a WhatsApp connection. For now the nightly job saves its report locally (`deliver local`), so nothing gets pushed to you and you'll see reminders when you next talk to the agent. Once WhatsApp is connected, you can point the job at it.
2. **Calendar.** The `google-workspace` skill is present but I didn't check whether it's set up. Until it is, `wt-schedule` will tell you it couldn't book time instead of silently doing nothing. Commitments still get tracked, and the steward's nightly check catches anything without a booked slot.

My first attempt at the base changes was committed as `agent:main`, and the weekly permissions audit would have flagged it. I reset the base to its first commit and redid the changes as you (`user`). The base is new and empty, so nothing was lost.

There was already a profile called `wt-steward` outside the aos-* namespace. I didn't touch it or count it. The file kb uses to list your bases (`.aos/kb-registry.yaml`) now includes `commitments`; kb manages that file itself.

### Evolve

The work-tracker steward is now set to run at 22:00 instead of 22:47. The change is saved in your MOD.md, so it will survive every upgrade.

- **Your settings:** in `personal/capabilities/work-tracker/MOD.md`, `steward_hour` changed from "22:47" to "22:00". I committed it myself (1ec939c) because nothing committed it automatically.
- **The job:** the `aos:work-tracker:nightly-steward` job in the aos-steward profile now has the schedule `0 22 * * *`. No skill text or the steward's persona file had 22:47 written in, so nothing else needed changing.
- **Checks:** I refreshed the recorded file fingerprints and the install check came back clean.

Two things to know:
- The job is paused, the same as before the change. Hermes still lists the next run as 22:47 tonight. That's most likely an old value left over from before the edit, which should update when the job is resumed. Say if you want it resumed.
- I only looked at the aos-* profiles (aos-steward, aos-archiver, aos-test). I didn't touch the other profiles, including the separate `wt-steward` one.

### Removal

I removed all three capabilities: work-tracker, then kb, then capability-lifecycle last, because the other two depend on it and its aos-cap tool does the record-keeping. The install record is now empty (`installs: {}`), and a final check found nothing left behind.

Removed:

  work-tracker
    - Its scheduled job aos:work-tracker:nightly-steward is gone.
    - Its 6 skill links in aos-test and aos-steward are gone.
    - Its 4 aos-steward config keys are unset.
    - The aos-steward profile is deleted. The capability created it (its install record holds aos-steward's SOUL.md, and the file was unchanged) and nothing else used it.

  kb
    - Its 3 scheduled jobs are gone, plus the leftover output of the sync job.
    - Its 8 skill links are gone.
    - Its 2 aos-archiver config keys are unset.
    - The script aos-archiver/scripts/aos-kb-sync.sh is deleted.
    - The aos-archiver profile is deleted, on the same grounds as aos-steward.
    - The kb tool (aos-kb) is uninstalled.

  capability-lifecycle
    - Its 11 skill links in aos-test are gone, including skill-creator.
    - Its two marker blocks are stripped from aos-test/SOUL.md. The rest of that file is unchanged.
    - The aos-cap tool is uninstalled.

  For each capability, the rendered skills folder was deleted in a dated commit in personal/ (1298242, 81fbcf6, e97730a). Reverting a commit brings that folder back.

Checks afterwards: no links into the household from any aos-* profile or ~/.hermes/skills, no aos: markers in aos-test, and no scheduled jobs.

I only touched aos-steward, aos-archiver and aos-test. Profiles outside aos-* (wt-steward, archiver, […] and the others) were left alone, even though some link to skills elsewhere under ~/aos.

The rules say to ask before removing a recorded .env line, and nobody could answer. The AOS_AGENT lines lived only in the two agent profiles, so they went when those profiles were deleted. Before deleting, I exported both profiles; they can be restored from:
  ~/.hermes/profiles/aos-test/cache/scratch/aos-steward-export.tar.gz
  ~/.hermes/profiles/aos-test/cache/scratch/aos-archiver-export.tar.gz
That folder clears out files left untouched for 24 hours, so copy them elsewhere if you want to keep them.

Kept, since the rules say to ask first:
  - Your answers (MOD.md) stay in personal/: MOD.md, capabilities/kb/MOD.md and capabilities/work-tracker/MOD.md. A reinstall comes back with your personalization.
  - .aos/kb-principal.yml is the list of who writes as you on this machine (dana@example.com). It's yours, so I didn't delete it.
  - .aos/kb-registry.yaml lists every knowledge base (personal-kb, acme-kb, commitments). It's also yours. The bases themselves under tests/.sandbox/kb/ were never touched.
  - vendor/anthropic-skills: the downloaded third-party copy of skill-creator. Nothing installed links to it any more, so you can drop it if you like.
  - The operator lines AOS_HOME and AOS_PRINCIPAL_ID in aos-test/.env were never part of an install record, so they were never on the removal list.

The aos-cap tool is uninstalled, so it's no longer available on this machine, and the capability-remove and related skill links are gone from aos-test.
