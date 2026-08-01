# Live e2e — the slot mechanism, on real Hermes (2026-07-31)

Run per `tests/golden/PROTOCOL.md` into a disposable `aos-test` profile. Hermes v0.19.0,
bedrock/claude-sonnet-5. Household: `tests/.sandbox/aos-home` (not `~/aos`).

**Canary clean** — `prestate.sh` before and after diffed empty, so the user's own profiles
(`archiver`, `hera`), root skills and 19 cron jobs were untouched.

## What this run proves that no re-render could

- ten lifecycle skills rendered, committed in `personal/`, symlinked (not copied)
- **two** context blocks on `SOUL.md`: `mode-boundary@0.3.5` and the new
  `concepts@0.3.5`, with `<home>` baked to the real household path. The golden sentinel
  that had been deliberately red since the concepts block was added is green because an
  agent wrote the block — not because a snapshot was hand-edited.
- **zero unresolved `{{skill:}}`/`{{agent:}}` slots** in any rendered file, and zero stale
  `aos-lock`. Cross-references read as real installed names (`capability-contribute`, …).
- `reference/naming.md`'s escaped examples **survived as literals**, so the file still
  teaches the syntax that rendered it. The self-reference trap, closed in reality.
- the agent computed `kb-archiver` from the manifest's prefix (the agent-naming mechanism)
  and ran `aos-cap verify` clean after `record` — both unprompted, from the prose alone.
- `aos-cap --home <sandbox> verify` → `clean: 2 entries verified` (58 artifacts, 19 links).

## Not proven here: work-tracker

The Day-N prompt (a fresh install with no bootstrap context) stalled three times with **zero
output** while the same profile answered trivial prompts normally. Diagnosis: 6s CPU over 6min
wall, state `S`, no session writes, no throttling in any log — blocked on the provider, not on
the kit. The two residual `check.mjs` failures are both "no lockfile entry for work-tracker",
i.e. the same single cause. The Day-N seam itself remains verified by the 2026-07-29 run.

## Install summary, as the agent reported it

The install was already complete from earlier work in this session lineage; I verified everything end-to-end and it's clean. Here's where things stand:

**capability-lifecycle 0.3.5** — the chicken-and-egg bootstrap BOOTSTRAP.md always does first:
- `aos-cap` tool on PATH, lockfile at `.aos/installs.lock.yaml`
- All 10 skills rendered into `personal/capabilities/capability-lifecycle/skills/`, symlinked into the `aos-test` front profile
- Global interview was already satisfied (Dana, Europe/Lisbon, auto-accept diff review)
- Mode-boundary + concepts context blocks appended to `aos-test`'s SOUL.md
- `skill-creator` vendored in from Anthropic's skills repo

**kb 0.7.2** — the capability you asked for:
- `aos-kb` tool on PATH → `kb 0.7.2 (layout 2)`
- `aos-archiver` Hermes profile created for the Archiver agent — only `terminal`/`file`/`skills` toolsets (no messaging/web/vision), matching `tools: [fs.read, fs.write, shell]`
- 7 skills rendered and symlinked: entry skill `kb` → both `aos-test` and `aos-archiver`; `kb-capture`/`kb-route`/`kb-recall`/`kb-init`/`kb-adopt`/`kb-import` → `aos-test` only
- Three schedules on `aos-archiver`: `aos:kb:nightly-promote` (23:30), `aos:kb:weekly-maintain` (Sat 07:00) as agent jobs, plus `aos:kb:sync` (*/5min) as a script-only exec job via `~/.hermes/scripts/aos-kb-sync.sh` — no model wakes up for that one
- `AOS_AGENT=agent:archiver` set in the archiver's `.env`; `AOS_REGISTRY` now also set in its config (I closed a gap here — it was recorded in the lockfile's `config_keys` but not yet actually set on the profile, so I set it)
- Both lockfile entries pass `aos-cap verify` clean, `personal/` git tree is clean

**Left open**, worth telling the user directly: `personal/kb-registry.yaml` lists `personal-kb` and `acme-kb`, but their paths (`~/aos/upstream/tests/.sandbox/kb/...`) don't resolve to anything on disk in this custom household — no base has actually been scaffolded. The machinery is fully wired; running `kb-init` or `kb-adopt` against those two registry entries is the natural next step whenever you want the archiver to have something to maintain.

Want me to continue with `kb-init`/`kb-adopt` to actually scaffold those bases, or hold there since you said work-tracker comes later as its own prompt?
step whenever you want the archiver to have something to maintain.
