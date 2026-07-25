# e2e — installed skill names + the merged capability-lifecycle (Hermes, real)

Hermes Agent v0.19.0 (2026.7.20). Disposable `aos-test` / `aos-drainer` / `aos-archiver`
profiles; household at `tests/.sandbox/aos-home` (upstream = a clone of
`skill-identity-and-lifecycle-merge`). Overlay seeded from `tests/fixtures/personal`,
`diff_review: auto-accept`.

## What this run had to prove

The name a skill installs under is computed, single-owner, and the same everywhere. Four
capabilities became three.

## Phases

**Bootstrap install** (`capability-lifecycle` inline, then `kb`). Two prompts: the first
stopped correctly because the seeded `personal/` repo had no git identity — the agent
refused to commit as an unknown author rather than inventing one. After configuring
`Dana Fixture <dana@example.com>`, it completed:

- Nine lifecycle skills rendered and linked: `capability-lifecycle`, `capability-install`,
  `capability-upgrade`, `capability-remove`, `capability-onboard`, `capability-import`,
  `capability-build`, `capability-contribute`, `capability-evolve`. 29 artifacts, 9 links.
- The entry skill installed **verbatim** — `skills/capability-lifecycle/`, not the old
  `capability-lifecycle-capability-lifecycle/` stutter.
- kb: 23 artifacts, 7 links, 3 schedules, `base` tool installed, `aos-archiver` created.
- The mode-boundary context block present under its marker,
  `aos:capability-lifecycle:mode-boundary@0.3.0` — and no identity block: the harness
  owns user context, so aos does not distil the user's facts into an agent it did not
  create.

**One identity, verified on disk:**

```
~/.hermes/profiles/aos-test/skills/kb-init -> …/personal/capabilities/kb/skills/kb-init
   (a symlink, not a copy)
head -4 …/skills/kb-init/SKILL.md → name: kb-init      x-aos-origin: kb@0.5.0
```

Dir == frontmatter `name` == render dir == link. Nothing rewrote a name per harness.

**The collision gate, tested against a real harness.** The `aos-test` profile carries ~20
Hermes-bundled skills (`email`, `github`, `research`, `productivity`, `note-taking`, …) —
the hazard is not hypothetical. With a decoy `gtd-drain/` skill planted in the profile, the
Day-N install stopped dead:

> Installation stopped at the mandatory name gate. Collision detected: `gtd-drain` from
> `gtd-capture:drain`, already claimed by an existing skill at
> `~/.hermes/profiles/aos-test/skills/gtd-drain`. `aos-lock` exited `17`, so per the install
> contract I did not render, modify the harness, create a profile, schedule a job, or alter
> the overlay. This must be resolved in the package/upstream […] never by renaming during
> installation.

Decoy removed → the same install completed: `gtd-capture`, `gtd-quick-capture`, `gtd-drain`,
`aos-drainer` profile, `aos:gtd-capture:nightly-drain` at 22:47 (the fixture's `drain_hour`).

**Evolve** (`change gtd-capture's drain schedule to 22:00`) → `drain_hour` updated in
`personal/capabilities/gtd-capture/MOD.md`, cron rewritten to `0 22 * * *`,
`aos-lock verify gtd-capture` clean.

**Removal** in the safe order (gtd-capture → kb → capability-lifecycle): every link, render,
job, wrapper, tool, and both `SOUL.md` marker blocks gone; three revertible commits in
`personal/`; MOD files preserved; both capability profiles deleted; `aos-lock list` empty.

**Canary**: `prestate.sh` byte-identical before the run, after removal, and after deleting
`aos-test`. Nothing outside the `aos-*` namespace was touched.

## Checks

- `node tests/golden/check.mjs --live full-install` → `golden: 0 failures`
- `node tests/golden/check.mjs` (snapshot mode, re-snapshotted) → `golden: 0 failures`
- `bash tools/check.sh` → tier 0 (54 + 71 tests) OK, 3 capabilities, 0 errors, 1 warning
  (`skill/all-main`, deliberate and documented in the manifest)

## Defects this run found, and fixed

1. **The mode-boundary block over-fired.** "Change gtd-capture's drain schedule to 22:00"
   tripped the MARS detector — the block said "before creating any cron job…" and an
   already-installed capability's schedule reads as a cron job. The block now carves out
   what its skill description already did: changing something aos installed is
   `capability-evolve`, not building. Re-run took the evolve path correctly.
2. **A MOD-only directory read as a shadowing package.** `personal/capabilities/gtd-capture/`
   exists for every capability the user has answers for, so the personal-first resolution
   rule reported a shadow on an ordinary install. The contract and `capability-install` now
   require a `CAPABILITY.md` before a directory counts as a source.
3. **A sentinel asserted verbatim prose the contract says to distill.** The drainer's SOUL.md
   carried the sacred-time constraint reworded ("Thursday choir practice, 19:00–21:00"), so
   the fixture's exact phrasing failed. The sentinel now matches the distinctive token — a
   verbatim assertion contradicted the contract it was testing.
4. **The normalizer leaked and bloated.** Pointing it at the whole household swallowed the
   `upstream/` clone, and the profile's own `home/` (the agent's npm/node sandbox, 735 files,
   8.4M) carried absolute developer paths into the snapshot. `home` and `lsp` are now skipped
   along with two harness marker files, and empty directories are pruned: 896K, no leaks.
5. **Protocol setup steps that were never written down.** A fresh profile has only
   `model.default` and dies with `Invalid length for parameter modelId`; the seeded
   `personal/` repo needs a git identity. Both are now in `PROTOCOL.md`.

## Second run — the cheat-sheet relocation (2026-07-25, same day)

Re-run in full after the cheat-sheets moved into the entry skill's `reference/`, because the
render's file set changes and the lockfile's artifact list is agent-decided. It proved the
fix: `personal/capabilities/capability-lifecycle/skills/capability-lifecycle/reference/`
contains all four `harness-*.md` files, so an installed skill reaches its cheat-sheet
without a path that only exists upstream. The expectations now assert that.

Three more ambiguities surfaced, each one a case of two runs reading the same rule
differently — which is the useful kind of e2e finding:

6. **`messaging.inbound: required` refused the install.** The `aos-test` profile had no
   messaging platform paired (it is seeded from a deliberately non-messaging worker
   profile), and the agent read a `required` host feature as "configured right now" rather
   than "the harness can express it" — which the Hermes sheet marks ✓. A `required` gate
   that flips on configuration state refuses installs that would work and makes the whole
   degraded-mode vocabulary pointless. The contract now says which reading is meant.
7. **kb's `exec:` sync schedule landed in a different profile than last run** — front this
   time, archiver before. An exec entry names no agent, so nothing said who hosts it. Now
   it is the agent that owns the capability's other schedules.
8. **The golden checks did not know about a referenced third-party skill.** `skill-creator`
   correctly carries no `x-aos-origin` (not ours to tag) and correctly links into `vendor/`
   rather than `personal/` — both of which the checks read as failures. `vendored:` in the
   expectations names them.

**The canary fired, and it was not us.** `~/.hermes/config.yaml`'s hash changed mid-run.
Investigated rather than waved off: the diff is a "Meridian" provider block and a default
model, with its own `config.yaml.bak-meridian-…` backup written at 15:54 — zero aos content
(no skills, cron, or profiles), and the three canary fields an install would actually touch
(profiles, root skills, root job ids) are byte-identical. An unrelated concurrent change in
the environment, not an install violation.

## Third run — no identity block (2026-07-25)

Re-run once more after the front agent's identity block was dropped: SOUL.md content is
agent-written, so only a live run can attest its *absence*. The agent's own staging summary
named "the single MARS mode-boundary block", and the installed file confirms it — one
aos-owned block, and zero occurrences of the fixture's identity facts (Lisbon, choir,
working hours, the user's name). The harness's own `memories/USER.md` is left to do what it
already does. `forbid_texts` in the expectations now asserts the identity marker and the
retired `aos:onboarding` one are both absent, so this cannot silently come back.

Canary byte-identical across the whole run.

## Snapshot provenance

Every file under `tests/golden/hermes/full-install/` comes from the third live run —
install, day-N — with no hand edits and no re-rendered shortcuts. (The first run's snapshot did carry nine tool-re-rendered skill directories, to
pick up two prose fixes found in review; the full re-run made that moot. `PROTOCOL.md`
keeps the rule for when that shortcut is legitimate, since it will come up again.)
`check.mjs` asserts a committed snapshot equals what `normalize.mjs` produces, so a file
updated by any path that skips the normalizer is caught.

## Observed, not fixed (out of scope)

The evolve run declined to commit the overlay change ("I did not commit without your
request") although the contract's persist hook says the agent commits, silently. Pre-existing
prose-adherence gap, unrelated to skill identity — noted for a later pass.
