---
name: capability-install
description: 'Installs an aos capability into this harness: reads its briefing, gates
  the skill names it would claim, renders it against the user''s MOD.md, and materializes
  agents, symlinks, schedules and context blocks behind a diff gate. Use when the
  user says "install" or "set up" and names a capability, offers a capability directory
  or CAPABILITY.md to install, or when another install needs a missing dependency
  installed first. Do NOT use to re-render an already-installed capability against
  fresher upstream — that is capability-upgrade — and not to change how an installed
  one behaves, which is capability-evolve. The interview it runs mid-install belongs
  to capability-onboard.'
metadata:
  aos:
    origin: capability-lifecycle@0.3.5
---
# capability-install

Not in context yet? Load the `capability-lifecycle` skill first — the map, the contract,
the overlay doctrine, and the Experience rules. Then:

1. Resolve the capability dir across the household — `personal/capabilities/<id>`
   first, then `upstream/capabilities/<id>`, counting a directory as a source **only if it
   holds a `CAPABILITY.md`** (a MOD-only directory is the user's overlay at its mirrored
   path, not a package); both are real packages → say so loudly and ask which
   (never silently prefer). Then `aos-cap manifest <dir>` → validated JSON. Validation
   failure → show the tool's error, offer fix-or-report; never improvise a parse.
2. `aos-cap show <id>`: installed at this version → say so, stop; older →
   hand to capability-upgrade.
3. Dependencies: each `depends.capabilities` missing from `aos-cap list` →
   announce briefly ("work-tracker needs kb — setting that up first"), install it first,
   its interview included.
4. Load your cheat-sheet **now** — it travels with the `capability-lifecycle`
   skill as `reference/harness-<harness-runtime>.md` (load that skill, then read the file;
   your harness runtime is the program hosting you). Feature notes first, and read them as
   what the *harness* can express, not as what the user has wired today (contract): a
   `required` feature the table marks unsupported → friendly stop with the reason; a
   supported-but-unconfigured channel → install, and say what they still need to set up;
   `preferred` unsupported → note each schedule's declared degraded mode for recording.
5. **Name gate**, before anything is written:
   `aos-cap --home <home> skills <dir> --check --harness-skills <each skills dir this
   harness reads, per the cheat-sheet's Primitive mapping>`. Read its `checked:` lines —
   a source it could not reach is named in capitals, and "clean" against two of three
   sources is not clean. Exit 17 → stop and report which name is
   taken and by whom; a collision is fixed in the package (capability-contribute, or the
   user's own source), never by renaming here. Clean → the printed installed names are
   what every later step uses (the `capability-lifecycle` skill's `reference/naming.md`).
   In the same breath, if the capability ships `agents/`:
   `aos-cap --home <home> agents <dir> --check` — agents land in a flat per-harness
   namespace too, so the same exit 17 and the same rule (fix the package, never rename
   here). It checks two of three sources; the third — agents already in the harness — has
   no enumeration yet and says so in capitals, so glance at what the harness already has.
6. Interview, iff the capability ships ONBOARDING.md — run it per the
   `capability-lifecycle` skill's `reference/overlay.md` (batched, typed validation, secrets → store per the
   cheat-sheet's Secrets section) → write `<home>/personal/capabilities/<id>/MOD.md`.
7. Render, then transform: `aos-cap render <dir> <skill-id> --out
   <home>/personal/capabilities/<id>/skills` per declared skill (mechanical — installed
   name, frontmatter `name`, `metadata.aos.origin`), then fill `{{mod}}` slots and bake `<home>`
   in the render per that same `reference/overlay.md`. Shipped files stay untouched.
8. **STAGE** per the cheat-sheet's Materialization guide: the render sits in
   `personal/`'s working tree (uncommitted) plus the exact native command plan —
   agents, skill symlinks (the installed name → the render, per `used_by`; container
   harness → verify the `<home>/personal` mount per the cheat-sheet), schedules
   (`aos:<cap>:<schedule-id>`, single-owner check first), context blocks (markers), config
   keys, the capability's own tool install line. Touch no harness file yet.
   Second-harness install: stage links + native plan only (the render already exists);
   schedules stay with their current owner unless the user reassigns.
9. **GATE**: show the full plan, payoff-framed — each artifact → what it does
   for the user. Wait (unless the root MOD.md says auto-accept).
10. **EXECUTE** the approved plan: commit the render in `personal/` (dated
   message — the persist hook), create the symlinks, run the native plan; `kb:`
   zones → draft grant rows into each target KB's `## Grants` table, user approves.
   A capability's tool may write its own machine-local file under `<home>/.aos/` on first
   use — kb's `kb-principal.yml` is the one today. Do **not** create it yourself: the tool
   owns it, the same way `aos-cap` owns the lockfile. Say it exists in the summary so
   the user is not surprised by a file nobody mentioned, and leave it out of `record`
   (machine-local state is not a materialized artifact — hashing it would report drift the
   first time the tool touched it).
11. `aos-cap record <id> --version <v> --source-root <root> --artifact
    <render-file>… --link <symlink>… --job <id>… --config-key <k>…` — `<root>` is
    whichever root step 1 resolved the capability dir in (`upstream` for shipped
    capabilities, `personal` for the user's own); render files go to `--artifact`
    (hashed), symlinks to `--link` (a symlink passed as `--artifact` fails: exit 16 — so a
    tool binary needs `readlink -f $(command -v <tool>)` first, since `uv tool install` puts a
    link on PATH). **`record` replaces the entry
    wholesale**: on a second-harness install, start from `aos-cap show <id>` and pass the
    combined set (both harnesses' links), never just this harness's.
12. `aos-cap verify <id>` — exit 13 means what you just recorded does not match what is
    on disk (a link that is a copy, a missed render, a hash taken before the transform).
    Fix it now: you still know what you wrote, and the next person to find out would be
    capability-upgrade, months from now.
13. Celebrate specifically: what, where, which schedules, degraded modes in effect.
