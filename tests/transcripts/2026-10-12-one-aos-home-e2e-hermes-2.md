# Full e2e, second run — sandboxed tools, real Hermes (2026-10-12)

`golden: 0 failures`, live and snapshot. Hermes v0.21.5 (2026.9.24), bedrock /
claude-opus-5-5, disposable `aos-test` / `aos-archiver` / `aos-steward` profiles, household at
`tests/.sandbox/aos-home`, upstream cloned from branch `one-aos-home` (`e132ceb`). It
re-records the golden snapshot for the same versions as the
[first run](2026-10-12-one-aos-home-e2e-hermes.md) (**kb 0.8.0 / capability-lifecycle 0.5.0 /
work-tracker 0.1.2**), now under the updated protocol:

- the run's `uv tool` calls go to `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR` under the sandbox, and the
  sandbox `bin` comes first on PATH, in the operator shell and in every `aos-*` profile
- the real tools are never backed up or restored, because nothing touches them
- no default-profile fallback
- the bootstrap `kb init` gets `--principal dana@example.com`

**Canary clean** after install, after removal and at the end (`prestate.sh` byte-identical).
A fingerprint of what the run must not change was taken at the start. It was re-checked after
the bootstrap, after the Day-N install, after removal and at the end, and was identical each
time. A 10-second watcher compared it throughout and logged no change. It covered:

- the operator's real household `.aos/` files (sha256)
- the real `personal/` HEAD and the HEADs of the three real bases
- `ls -la` of the real `aos-kb`/`aos-cap` uv tool dirs and their `~/.local/bin` links
- the sha256 of their `uv-receipt.toml` and every `RECORD`
- `kb --version` / `aos-cap --version` (`kb 0.8.0 (layout 2)`, `aos-cap 0.5.0`)

**This time the real tools never changed**, which is the point of the protocol change. The
lockfile now records the tool binaries at `<sandbox>/uv/tools/aos-cap/bin/aos-cap` and
`<sandbox>/uv/tools/aos-kb/bin/kb`. The first run recorded `~/.local/share/uv/tools/…`.

## Timeline

| step | prompt / command | start → end | exit |
|---|---|---|---|
| 1 prestate | `prestate.sh` → `tests/.sandbox/prestate.txt` | 21:30 | 0 |
| 2 profile | `hermes profile create --no-alias aos-test`, working `config.yaml` + credential lines + the five pin lines in `.env` | 21:30 | 0 |
| 2 smoke #1 | print `AOS_HOME`, `UV_TOOL_DIR`, `UV_TOOL_BIN_DIR`, first PATH entry, `AOS_PRINCIPAL_ID` | 21:31:55 → 21:32:34 | 0, **first PATH entry `~/.local/bin`** (finding 1) |
| 2 smoke #2 | same, after `terminal.shell_init_files` + `<sandbox>/path.sh` | 21:33:43 → 21:33:53 | 0, first entry `<sandbox>/uv/bin` |
| 3 bootstrap | PROTOCOL step-3 prompt, verbatim | 21:34:28 → 21:41:46 | 0 |
| 3 Day-N | `install work-tracker from the aos household at <sandbox>/aos-home.` + namespace sentence | 21:42:50 → 21:55:47 | 0 |
| 4 check | `aos_lint.golden.check --live full-install` | 21:55 | 0 (`golden: 0 failures`) |
| 4 canary | `prestate.sh` diff · `aos-cap --home <sandbox>/aos-home verify` | 21:55 | identical · `clean: 3 entries verified` |
| 5 snapshot | `aos_lint.golden.normalize` × 4 roots, into emptied `front/` `archiver/` `steward/` `home/` | 21:56:07 → 21:56:08 | 0 |
| 5 pause | `hermes -p <profile> cron pause <id>` × 4 jobs | 21:56:19 → 21:56:40 | 0 |
| 5 evolve | `change work-tracker's steward hour to 22:00.` + namespace sentence | 21:56:46 → 21:57:31 | 0 |
| 5 re-check | `aos-cap verify` · job state | 21:57 | `clean: 3 entries verified` · paused |
| 6 remove | removal prompt (below) + namespace sentence | 21:58:11 → 22:00:47 | 0 |
| 6 canary | `prestate.sh` diff · lockfile · real fingerprint | 22:01 | identical · `installs: {}` · identical |
| teardown | test `aos-test` deleted, borrowed `aos-test` restored and verified | 22:01:07 → 22:03:02 | 0 |

The pin lines went into `aos-archiver/.env` at 21:38:40 and `aos-steward/.env` at 21:52:42,
together with the credential lines and the `shell_init_files` key, within about 2 s of each
profile's `config.yaml` and `.env` appearing. Before the snapshot, `aos:kb:sync` ticked three
times (21:45, 21:50, 21:55), all against the sandbox registry:
`personal-kb: skipped (sync: none)`, `acme-kb: skipped (sync: none)`.

The removal prompt: *"remove every capability installed from the aos household at
`<sandbox>/aos-home` — work-tracker, kb and capability-lifecycle — per capability-remove and
the Hermes cheat-sheet's Removal section."* + the namespace sentence.

The evolve prompt's namespace sentence was the Day-N one: *"Agents go in aos-&lt;agent id&gt;
profiles; profiles outside aos-\* are another household's — never adopt, modify or count
them."*

## Verified in this run

- **the tools stayed in the sandbox**: both `uv tool install`s landed in `<sandbox>/uv/`, and
  removal's `uv tool uninstall`s emptied it, leaving an empty `<sandbox>/uv/bin` and no
  `<sandbox>/uv/tools`. The real `aos-kb`/`aos-cap` were not involved at any step
- **identity from the typed flag**: the bootstrap's `kb init --principal dana@example.com`
  wrote `.aos/kb-principal.yml` with the current header ("fills it in when missing").
  `personal/capabilities/kb/MOD.md` no longer gets an agent-added `principal_id` (first
  run, finding 4). Every `personal/` commit is authored by Dana Fixture
- **the sync wrapper pins the household and the tools**: it exports `AOS_HOME=<sandbox>/aos-home`,
  `AOS_AGENT=agent:archiver` and `PATH=<sandbox>/uv/bin:$PATH`, then runs `exec kb sync --all`.
  It sits in `aos-archiver/scripts/`, which the 0.21 cheat-sheet now says
- the Day-N seam: a fresh prompt triggered the materialized `capability-install` and created
  `aos-steward`, the `commitments` base and `aos:work-tracker:nightly-steward` at
  `47 22 * * *`
- evolve: `steward_hour` 22:47 → 22:00 in `personal/capabilities/work-tracker/MOD.md`
  (`499f948`, Dana Fixture). The job was edited to `0 22 * * *` and stayed paused, and
  `aos-cap verify` was clean
- removal walked each lockfile entry backwards, in reverse dependency order. It deleted both
  agent profiles it had created, and the `aos-steward` command alias with them. It kept the
  user data: the MOD files, the bases, `kb-principal.yml`, `kb-registry.yaml` and
  `vendor/anthropic-skills`
- the two `capability-install` renders (`front:` link target and `home:personal/…`) carry
  `e132ceb`'s text ("`kb init --principal` fills in a missing one"), and so do
  `contract.md`, `harness-hermes.md`, `harness-claude-code.md`, `no-cheatsheet.md`,
  `capability-remove`, `capability-upgrade` and `kb-init`

## Findings

1. **The `.env` PATH line does not reach the terminal tool's PATH** (protocol defect, fixed in
   PROTOCOL step 2). Hermes 0.21's terminal tool builds its env from a login-shell snapshot
   that sources `~/.profile`, `~/.bash_profile` and `~/.bashrc`. A stock `~/.profile`
   prepends `~/.local/bin` (and `~/bin`), so the first smoke test printed `~/.local/bin` as
   the first PATH entry, and every `kb`/`aos-cap` call would have resolved the machine's own
   tools.
   - `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR` *did* arrive, so the tools would still have been
     installed into and uninstalled from the sandbox.
   - But the install would have executed and recorded the real binaries. The sync wrapper
     would also have carried their path into the snapshot.
   - Fix: a `<sandbox>/path.sh` holding `export PATH="<sandbox>/uv/bin:$PATH"`, listed last
     in each `aos-*` profile's `terminal.shell_init_files` (`hermes -p <profile> config set`).
     An explicit list replaces the auto-sourced one, so it names the three rc files too.
     The second smoke test printed `<sandbox>/uv/bin` first.
   - The file sits outside `<sandbox>/uv/`, which removal empties.
   - `config.yaml` is never snapshotted, so the key does not reach the golden.
2. **New Hermes runtime files in the front profile** (normalizer extended, the snapshot
   pruned to match). The copied `config.yaml` names a memory provider, so Hermes installed
   that plugin's whole source tree into `aos-test/plugins/` on the first start. The tree
   includes `__pycache__`, and the dir also holds `.install-metadata.json`. Hermes also
   wrote `source-checks/<install-id>.json`, which holds the Hermes checkout's identity with
   absolute paths, and `.mcp-discovery.lock`. None of these are install artifacts.
   - `SKIP` gains `source-checks` and `.mcp-discovery.lock`. A `plugins/` dir is dropped only
     when it holds the plugin-store marker, because `plugins` is too generic for a basename
     rule.
   - The evolve step had already started when this surfaced, so the snapshot could not be
     re-normalized from the pre-evolve trees. The three paths were deleted from it instead,
     which is exactly what the extended normalizer prunes.
   - To prove that, the extended normalizer was run over the post-evolve live trees into a
     scratch dir, and `diff -r` against the committed snapshot. The only differences were
     the four jobs' `enabled`/`state`/`paused_at` (the pause), `steward_hour` in the
     work-tracker MOD and the steward job's `expr`/`display` (the evolve). No other file
     differs.
3. **Day-N: one long quiet stretch.** From 21:43 to 21:52 the process showed no child
   processes, no new commits and about 11 s of CPU, with one TLS connection open to the
   provider. It was model latency, not a hang: the work resumed and finished at 21:55:47.
   The `auth.lock` hang the protocol warns about looks the same, and `ps -o wchan` alone did
   not tell the two apart. What did was the thread list, where new request threads kept
   appearing.
4. **Day-N self-correction, again.** The first pass recorded the base's config changes as
   `agent:main`, and lint reported 4 critical grant errors. The agent reset the fresh base
   and redid them as the user, the same as in the first run (finding 5 there).
5. **Agent-decided divergences from the first run.** They are run variance, not failures:
   the structural checks pass.
   - The archiver got no `timezone` config key, so the `aos:kb:*` jobs run on the
     machine's local time. The steward did get `timezone` (Europe/Lisbon), so in one run one agent has
     the user's timezone and the other does not.
   - The steward job now `deliver`s to the fixture's WhatsApp placeholder (normalized to
     `whatsapp:+<ID>`) instead of `local`, and names `wt-steward` as its skill.
   - Both agent SOULs were rewritten in third person.
   - The archiver's `.env` `AOS_HOME` line is now a recorded `env_lines` entry.
6. **Evolve: the agent committed the MOD change itself again** (`499f948`). It did not say
   whether a persist hook ran. Step 5 expects the hook to make that commit, as in the first
   run (finding 6 there). The agent noticed that the paused job's `next_run_at` still read
   22:47 and flagged it rather than resuming the job, as in the first run.
7. **Capture mode was not driven separately.** The evolve change was already in the ledger
   and committed, which leaves capture mode's fold step nothing to fold.
8. **Restoring the borrowed `aos-test`** (PROTOCOL step 6 now says how). `hermes profile
   delete` writes a tombstone at `profiles/.deleted/aos-test`. Until the tombstone is
   removed, Hermes reports the restored directory as `Profile 'aos-test' does not exist`.
   - Extracting without `-p` brought back umask-shaped modes. Re-extracting with `tar -xpzf`
     made `tar -dzf` against the archive clean apart from `state.db-shm`.
   - Within seconds the live dashboard process reopened the profile, writing its logs and
     `state.db*`. That is expected while the dashboard holds the deleted WAL inode (first
     run, finding 8).
   - Restored: 2173 entries before and after, and `config get model` unchanged.

## Snapshot

Still 142 files (`front/` 62, `archiver/` 7, `steward/` 5, `home/` 68), all from this live
run. Nothing was re-rendered with `aos-cap render`. Three runtime paths were pruned to
normalizer parity (finding 2). There are 33 modified files and no additions or deletions:

- 16 are kit prose that `e132ceb` changed. They appear twice (`front:` dereferenced link and
  `home:personal/` render) and cover the five `capability-lifecycle` files plus
  `capability-remove`, `capability-upgrade` and `kb-init`.
- `kb-principal.yml` has the new header.
- The lockfile has the sandbox tool paths and the config-key and `env_lines` changes.
- The registry has an agent-worded `commitments` purpose.
- `kb/MOD.md` is without `principal_id`.
- The rest are agent-decided renders: the `wt-*` MOD weaving, both SOULs, both jobs files and
  the sync wrapper.

## Agent reports, verbatim

The only edits are [the redaction pass](README.md): operator paths became `~`.

### Bootstrap install

kb and the capability-lifecycle kit are both installed in the aos-test profile, and `aos-cap verify` reports both lockfile entries clean. Your MOD.md sets diff_review to auto-accept, so I staged each render in personal/ and committed it without stopping to wait for approval. work-tracker is not installed yet; that's the next prompt.

What landed:

1. Prerequisites and household
   - git 2.43 and uv 0.9.26 are present.
   - The upstream clone is clean and was not touched. personal/ already had its identity set (dana@example.com).
   - `aos-cap` is installed in the sandbox uv dir, and `aos-cap init` created `.aos/installs.lock.yaml`.

2. capability-lifecycle 0.5.0
   - The name check passed. The 10 skills are rendered into `personal/capabilities/capability-lifecycle/skills/`, committed, and symlinked into `~/.hermes/profiles/aos-test/skills/`.
   - Two marker blocks were added to the end of `aos-test/SOUL.md`: the mode boundary and the aos concepts (household path filled in). Nothing outside the markers was changed.
   - skill-creator is a shallow clone of anthropics/skills at `aos-home/vendor/anthropic-skills` (commit dbd4588), linked into the profile's skills, not copied.
   - The global interview didn't need to run again because `personal/MOD.md` already exists.

3. kb 0.8.0
   - The `kb` tool is installed in the sandbox uv dir.
   - The 7 skills are rendered into `personal/capabilities/kb/skills/` with the household path filled in, and committed. All 7 are linked into aos-test; the archiver gets only the `kb` skill.
   - The agent profile `aos-archiver` is newly created. It has its own SOUL.md (its purpose plus the concepts text). Its `.env` holds `AOS_HOME` and `AOS_AGENT=agent:archiver`. Its toolsets are limited to terminal, file, skills and todo for both the cli and cron platforms, so it has no messaging tools.
   - Two bases were created with `kb init`. Both lint with 0 Critical and 0 Findings.
     - personal-kb: the default base, private. This run passed `--principal dana@example.com`, which created `.aos/kb-principal.yml`.
     - acme-kb: shared.
   - The templates already include the archiver's zone grants on both bases, confirmed with `kb grants check`.
   - Three schedules run on aos-archiver:

     | Job | Schedule | Kind | Job id |
     |---|---|---|---|
     | aos:kb:nightly-promote | 23:30 daily | agent job | fd37298ea0cb |
     | aos:kb:weekly-maintain | Saturday 07:00 | agent job | 05e36e139122 |
     | aos:kb:sync | every 5 minutes | script only, runs `aos-archiver/scripts/aos-kb-sync.sh`, no model | 85db4cfa053f |

     The two agent jobs run with the `kb` skill and `AOS_AGENT=agent:archiver`.
   - The lockfile entry records the renders, the tool binary, the archiver SOUL.md (which marks the profile as created by this install), the links, the three job ids, the config keys, the `.env` variable names and the script.

Things to know:
- The bases sync nothing. The registry file you pre-seeded says `sync: none` for both, and `kb init` kept those entries, while kb's MOD.md says `manual`. Either way `kb sync` skips both bases, which is correct since neither has a remote. Switching to the 5-minute git sync needs a remote first.
- I created, changed or counted no profiles outside `aos-*`. aos-test has no cron jobs.
- No pushes, forks or remotes were created. A private remote for personal/ is still something you can add if you want one; contributing upstream later would mean a fork, and I haven't made one.
- Day-N: work-tracker, as its own prompt. Its steward will be created as the profile `aos-steward`.

### Day-N install

I've installed work-tracker 0.1.2. `aos-cap verify` comes back clean, and a test run against a throwaway copy of the new commitments base worked from start to finish with no lint errors. Your root MOD.md sets `diff_review: auto-accept`, so I went ahead without stopping for approval.

What you now have:

- **Skills for your main agent (aos-test):** `work-tracker`, `wt-capture`, `wt-schedule` and `wt-update`. When you say "I need to…" or "find me two hours for…", they file the commitment and schedule it right away.
- **A new steward profile, `aos-steward`:** it holds `work-tracker` and `wt-steward`, and every write it makes to the base is recorded under its own name (`agent:steward`). Its tools are limited to terminal, file, skills and todo, and its timezone is set to Europe/Lisbon.
- **Nightly schedule:** `aos:work-tracker:nightly-steward` runs at 22:47 Lisbon time, delivers to `whatsapp:+000000000000`, and sends nothing on a clean night.
- **The `commitments` base** (private), at `~/aos/upstream/tests/.sandbox/kb/commitments`, with the four required changes made:
  - an `actions` zone, plus its rules file at `actions/AGENTS.md`
  - the `action` page type
  - the eight extra page fields
  - write permission for both `agent:main` and `agent:steward`

  I recorded these changes under your own name (`user`), since they're yours to approve. My first attempt recorded them as `agent:main`, which made the base's lint report 4 critical grant errors. So I reset the new, still-empty base and redid the changes under your name; lint now shows 0 critical, 0 other findings.

Your answers are built into the skills:
- Every capture is confirmed with just 🦜, and the commitment is never repeated back to you.
- Titles start with the verb, and the deadline goes in the title when there is one.
- Estimates are in 30-minute steps, and time blocks go on your personal calendar.
- Nothing is ever booked over choir practice (Thursdays 19:00–21:00). If a slot clashes, you're told and offered the next free window.
- Waiting items are raised after 14 days, finished items are deleted after 90, and anything rescheduled 3 times gets questioned.

Things you should know:
- **WhatsApp:** the nightly report and reminders go to a placeholder number. They'll only reach you once WhatsApp is connected for that target.
- **Calendar:** time blocks need a calendar skill. `google-workspace` is enabled on the main agent, so this should work. If it doesn't connect, commitments are still tracked without blocks, and the steward's nightly check for unscheduled items picks them up.
- **Permission labels:** the two permission entries are tagged `via: work-tracker@0.1.0`, as the package's install instructions say, even though the installed version is 0.1.2. This doesn't affect anything now; it only matters if those entries are later removed by version.
- **Other profiles:** I created only `aos-steward` and touched nothing outside the aos-* profiles. There's an unrelated `wt-steward` profile on this machine, and I left it alone.
- **Files the kb tool wrote:** `kb` added a `commitments` entry to `<home>/.aos/kb-registry.yaml`. That file is machine-local and the tool owns it.

The skill files are in `~/aos/upstream/tests/.sandbox/aos-home/personal/capabilities/work-tracker/skills`, saved in commit `b29be59`.

### Evolve

work-tracker's nightly steward is now set to 22:00. I saved the change in your MOD.md, so it will carry over to every future upgrade.

What I changed:
- In your MOD.md (`personal/capabilities/work-tracker/MOD.md`), I changed the `steward_hour` answer from "22:47" to "22:00" in place and committed it (499f948).
- I moved the steward's scheduled job (`aos:work-tracker:nightly-steward`, c91b7e2a83a2) to `0 22 * * *` using `hermes cron edit`. That job belongs to the aos-steward profile.
- I refreshed the lockfile's recorded hashes, and the check afterwards came back clean (1 entry verified).

The job is paused. That was already the case before this change and I didn't resume it. Its "next run" still shows the old 22:47 time; I expect it to update to 22:00 when you resume the job, but I haven't checked that.

I only touched aos-* profiles. The other profiles, including the similarly named `wt-steward`, were left alone.

### Removal

All three are uninstalled: work-tracker, kb and capability-lifecycle. The lockfile is now empty (`installs: {}`), and I removed each one in reverse dependency order, following its lockfile entry and the cheat-sheet's Removal steps. Your answers in MOD.md are kept, so a reinstall comes back personalized.

What was removed:

  work-tracker
    - Its nightly-steward cron job.
    - 6 skill links: 2 in aos-steward, 4 in aos-test.
    - Its 3 config keys: platform_toolsets.cli, platform_toolsets.cron and timezone.
    - The aos-steward profile, which this install created. Its .env line went with it, and so did its gateway and its `aos-steward` command alias.

  kb
    - Its 3 cron jobs (nightly-promote, weekly-maintain, sync) and their output.
    - 8 skill links: 1 in aos-archiver, 7 in aos-test.
    - Its 2 config keys and the aos-kb-sync.sh script.
    - The aos-archiver profile, which this install created. Its .env lines and its gateway went with it.
    - The `kb` tool (uninstalled with uv).

  capability-lifecycle
    - 11 skill links in aos-test, including the third-party skill-creator link.
    - The two marker blocks in aos-test's SOUL.md (mode-boundary and concepts). The rest of SOUL.md is unchanged.
    - The `aos-cap` tool, uninstalled last because the bookkeeping needed it.

The skill copies in your personal repo were each deleted in a separate dated commit, so any of them can be undone with git revert: 5dd3e80 (work-tracker), f7d6d3e (kb), 0022432 (capability-lifecycle).

Checks afterwards: aos-test is the only aos-* profile left. It has no cron jobs, no skill links into the household and no aos marker blocks. I didn't touch any profiles outside aos-*.

Kept, because I couldn't ask you and deleting them can't be undone:
  - `.aos/kb-principal.yml` (who writes on this machine, dana@example.com) and `.aos/kb-registry.yaml` (your list of bases: personal-kb, acme-kb, commitments). A reinstall would pick these up again without asking. The bases themselves were never touched.
  - The skill-creator source folder at `vendor/anthropic-skills`. Nothing links to it any more.
  - aos-test's `.env` lines AOS_HOME and AOS_PRINCIPAL_ID. They aren't in any lockfile entry, so they don't look like they came from these installs.

All three are in `~/aos/upstream/tests/.sandbox/aos-home`. Say if you want any of them removed.
