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
- Both context blocks present under discriminated markers:
  `aos:capability-lifecycle:identity@0.3.0` and `…:mode-boundary@0.3.0`.

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

## Snapshot provenance

Every file under `tests/golden/hermes/full-install/` came from this run, except the nine
`capability-lifecycle` skill directories under `front/skills/` and
`home/personal/capabilities/capability-lifecycle/skills/`. Those were re-rendered with
`aos-lock render` (then `normalize.mjs`) after review found two prose defects baked into the
originals — a hand-off sentence broken by a merge substitution, and two skill bodies still
titled after deleted capabilities. Legitimate because these skills are `{{mod}}`-slot-free,
so the render is deterministic: verified by rendering the untouched `remove` skill and
confirming byte identity with the committed snapshot before regenerating the rest.
`check.mjs` now asserts that re-normalizing a snapshot is a no-op, which is what caught the
first attempt at this (it bypassed the normalizer and left a literal date where `<DATE>`
belongs). Everything agentic in the snapshot — placement, symlinks, schedules, context
blocks, the lockfile — is untouched from the live run.

## Observed, not fixed (out of scope)

The evolve run declined to commit the overlay change ("I did not commit without your
request") although the contract's persist hook says the agent commits, silently. Pre-existing
prose-adherence gap, unrelated to skill identity — noted for a later pass.
