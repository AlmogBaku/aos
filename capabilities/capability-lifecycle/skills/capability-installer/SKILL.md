---
name: capability-installer
description: Installs an aos capability into this harness. Use when the user says "install <capability>", offers a capability directory or CAPABILITY.md for installation, or another install needs a missing dependency installed first.
---

# capability-installer

Not in context yet? Load the `capability-lifecycle` skill first — the map, the contract,
the overlay doctrine, and the Experience rules. Then:

1. **[D]** Resolve the capability dir across the household — `personal/capabilities/<id>`
   first, then `upstream/capabilities/<id>`; both exist → say so loudly and ask which
   (never silently prefer). Then `aos-lock manifest <dir>` → validated JSON. Validation
   failure → show the tool's error, offer fix-or-report; never improvise a parse.
2. **[D]** `aos-lock show <id>`: installed at this version → say so, stop; older →
   hand to `capability-upgrader`.
3. **[D]** Dependencies: each `depends.capabilities` missing from `aos-lock list` →
   announce briefly ("kb needs onboarding — setting that up first"), install it first,
   its interview included.
4. **[D]** Load `harnesses/<harness-runtime>.md` (this capability) **now** — Feature
   notes first: a `required` host feature missing → friendly stop with the reason;
   `preferred` missing → note each schedule's declared degraded mode for recording.
5. **[A]** Interview, iff the capability ships ONBOARDING.md — run it per
   `reference/overlay.md` (batched, typed validation, secrets → store per the
   cheat-sheet's Secrets section) → write `<home>/personal/capabilities/<id>/MOD.md`.
6. **[A]** Transform per `reference/overlay.md`: original skills × MOD.md → the pinned
   render in `<home>/personal/capabilities/<id>/skills/…` ({{mod}} slots filled,
   `<home>` baked, shipped files untouched).
7. **[A]** **STAGE** per the cheat-sheet's Materialization guide: the render sits in
   `personal/`'s working tree (uncommitted) plus the exact native command plan —
   agents, skill symlinks (`<capability>-<id>` → the render, per `used_by`;
   `x-aos-origin` inside the render's frontmatter; container harness → verify the
   `<home>/personal` mount per the cheat-sheet), schedules (`aos:<cap>:<schedule-id>`,
   single-owner check first), context blocks (markers), config keys, the capability's
   own tool install line. Touch no harness file yet.
   Second-harness install: stage links + native plan only (the render already exists);
   schedules stay with their current owner unless the user reassigns.
8. **[D]** **GATE**: show the full plan, payoff-framed — each artifact → what it does
   for the user. Wait (unless the root MOD.md says auto-accept).
9. **[D]** **EXECUTE** the approved plan: commit the render in `personal/` (dated
   message — the persist hook), create the symlinks, run the native plan; **[A]** `kb:`
   zones → draft grant rows into each target KB's `## Grants` table, user approves.
10. **[D]** `aos-lock record <id> --version <v> --source-root <the root step 1 resolved
    the capability dir in — `upstream` for shipped capabilities, `personal` for the
    user's own> --artifact <render-file>… --link <symlink>… --job <id>… --config-key <k>…`
    — the tool hashes files and reads link targets itself. **`record` replaces the entry
    wholesale**: on a second-harness install, start from `aos-lock show <id>` and pass the
    combined set (both harnesses' links), never just this harness's.
11. Celebrate specifically: what, where, which schedules, degraded modes in effect.
