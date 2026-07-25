---
name: install
description: Installs an aos capability into this harness. Use when the user says "install" and names a capability, offers a capability directory or CAPABILITY.md for installation, or another install needs a missing dependency installed first.
---

# capability-install

Not in context yet? Load the `capability-lifecycle` skill first — the map, the contract,
the overlay doctrine, and the Experience rules. Then:

1. **[D]** Resolve the capability dir across the household — `personal/capabilities/<id>`
   first, then `upstream/capabilities/<id>`, counting a directory as a source **only if it
   holds a `CAPABILITY.md`** (a MOD-only directory is the user's overlay at its mirrored
   path, not a package); both are real packages → say so loudly and ask which
   (never silently prefer). Then `aos-lock manifest <dir>` → validated JSON. Validation
   failure → show the tool's error, offer fix-or-report; never improvise a parse.
2. **[D]** `aos-lock show <id>`: installed at this version → say so, stop; older →
   hand to `capability-upgrade`.
3. **[D]** Dependencies: each `depends.capabilities` missing from `aos-lock list` →
   announce briefly ("gtd-capture needs kb — setting that up first"), install it first,
   its interview included.
4. **[D]** Load your cheat-sheet **now** — it travels with the `capability-lifecycle`
   skill as `reference/harness-<harness-runtime>.md` (load that skill, then read the file;
   your harness runtime is the program hosting you). Feature
   notes first: a `required` host feature missing → friendly stop with the reason;
   `preferred` missing → note each schedule's declared degraded mode for recording.
5. **[D]** **Name gate**, before anything is written:
   `aos-lock --home <home> skills <dir> --check --harness-skills <each skills dir this
   harness reads, per the cheat-sheet's Primitive mapping>`. Read its `checked:` lines —
   a source it could not reach is named in capitals, and "clean" against two of three
   sources is not clean. Exit 17 → stop and report which name is
   taken and by whom; a collision is fixed in the package (`capability-contribute`, or the
   user's own source), never by renaming here. Clean → the printed installed names are
   what every later step uses (the `capability-lifecycle` skill's `reference/naming.md`).
6. **[A]** Interview, iff the capability ships ONBOARDING.md — run it per the
   `capability-lifecycle` skill's `reference/overlay.md` (batched, typed validation, secrets → store per the
   cheat-sheet's Secrets section) → write `<home>/personal/capabilities/<id>/MOD.md`.
7. **[A]** Render, then transform: `aos-lock render <dir> <skill-id> --out
   <home>/personal/capabilities/<id>/skills` per declared skill (mechanical — installed
   name, frontmatter `name`, `x-aos-origin`), then fill `{{mod}}` slots and bake `<home>`
   in the render per that same `reference/overlay.md`. Shipped files stay untouched.
8. **[A]** **STAGE** per the cheat-sheet's Materialization guide: the render sits in
   `personal/`'s working tree (uncommitted) plus the exact native command plan —
   agents, skill symlinks (the installed name → the render, per `used_by`; container
   harness → verify the `<home>/personal` mount per the cheat-sheet), schedules
   (`aos:<cap>:<schedule-id>`, single-owner check first), context blocks (markers), config
   keys, the capability's own tool install line. Touch no harness file yet.
   Second-harness install: stage links + native plan only (the render already exists);
   schedules stay with their current owner unless the user reassigns.
9. **[D]** **GATE**: show the full plan, payoff-framed — each artifact → what it does
   for the user. Wait (unless the root MOD.md says auto-accept).
10. **[D]** **EXECUTE** the approved plan: commit the render in `personal/` (dated
   message — the persist hook), create the symlinks, run the native plan; **[A]** `kb:`
   zones → draft grant rows into each target KB's `## Grants` table, user approves.
11. **[D]** `aos-lock record <id> --version <v> --source-root <root> --artifact
    <render-file>… --link <symlink>… --job <id>… --config-key <k>…` — `<root>` is
    whichever root step 1 resolved the capability dir in (`upstream` for shipped
    capabilities, `personal` for the user's own); render files go to `--artifact`
    (hashed), symlinks to `--link` (a symlink passed as `--artifact` fails: exit 16). **`record` replaces the entry
    wholesale**: on a second-harness install, start from `aos-lock show <id>` and pass the
    combined set (both harnesses' links), never just this harness's.
12. Celebrate specifically: what, where, which schedules, degraded modes in effect.
