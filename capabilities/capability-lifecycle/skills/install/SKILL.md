---
name: install
description: "Installs an aos capability into this harness: reads its briefing, gates the skill names it would claim, renders it against the user's MOD.md, and materializes agents, symlinks, schedules and context blocks behind a diff gate. Use when the user says \"install\" or \"set up\" and names a capability, offers a capability directory or CAPABILITY.md to install, or when another install needs a missing dependency installed first. Do NOT use to re-render an already-installed capability against fresher upstream — that is capability-upgrade — and not to change how an installed one behaves, which is capability-evolve. The interview it runs mid-install belongs to capability-onboard."
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
   Then hold the briefing to the declarations: it may say *how* to wire things, never
   *where* — a briefing that places something the manifest does not declare ("a dedicated
   profile", "every profile that calls me") → stop and report a package defect (contract).
2. `aos-cap show <id>`: installed at this version → say so, stop; older →
   hand to {{skill: upgrade}}.
3. Dependencies: each `depends.capabilities` missing from `aos-cap list` →
   announce briefly ("work-tracker needs kb — setting that up first"), install it first,
   its interview included. Every `uses` provider is a dependency, so it is installed by now;
   its `uses[].installed_name` comes from the manifest JSON.
4. Load your cheat-sheet **now** — it travels with the `capability-lifecycle`
   skill as `reference/harness-<harness-runtime>.md` (load that skill, then read the file;
   your harness runtime is the program hosting you). Feature notes first, and read them as
   what the *harness* can express, not as what the user has wired today (contract): a
   `required` feature the table marks unsupported → friendly stop with the reason; a
   supported-but-unconfigured channel → install, and say what they still need to set up;
   `preferred` unsupported → note each schedule's declared degraded mode for recording.
5. **Name gate**, before anything is written:
   `aos-cap --home <aos_home> skills <dir> --check --harness-skills <dir> …` — one
   `--harness-skills` per skills dir this harness reads, per the cheat-sheet's Primitive
   mapping. Read its `checked:` lines —
   a source it could not reach is named in capitals, and "clean" against two of three
   sources is not clean. Exit 17 → stop and report which name is
   taken and by whom; a collision is fixed in the package ({{skill: contribute}}, or the
   user's own source), never by renaming here. Clean → the printed installed names are
   what every later step uses (the `capability-lifecycle` skill's `reference/naming.md`).
   In the same breath, if the capability ships `agents/`:
   `aos-cap --home <aos_home> agents <dir> --check` — agents land in a flat per-harness
   namespace too, so the same exit 17 and the same rule (fix the package, never rename
   here). It checks two of three sources; the third — agents already in the harness — has
   no enumeration yet and says so in capitals, so glance at what the harness already has.
6. Interview, iff the capability ships ONBOARDING.md — run it per the
   `capability-lifecycle` skill's `reference/overlay.md` (batched, typed validation, secrets → store per the
   cheat-sheet's Secrets section) → write `<aos_home>/personal/capabilities/<id>/MOD.md`
   (capability-lifecycle's own: `<aos_home>/personal/MOD.md` — the `capability-lifecycle` skill's
   `reference/overlay.md`, Which MOD.md).
7. Render, then transform: `aos-cap render <dir> <skill-id> --out
   <aos_home>/personal/<render-path>/skills` per declared skill — `<render-path>` is
   `capabilities/<id>` for a shipped package and `renders/<id>` for the user's own (whose
   `capabilities/<id>/` is the source; `render` refuses an output inside its source) —
   mechanical: installed name, frontmatter `name`, `metadata.aos.origin`. Then the
   transform per the `capability-lifecycle` skill's `reference/overlay.md`, against this
   capability's MOD.md (Which MOD.md): fill `{{mod}}` slots, weave its prose statements,
   bake `<aos_home>`.
   Source files stay untouched.
8. **STAGE** per the cheat-sheet's Materialization guide: the render sits in
   `personal/`'s working tree (uncommitted) plus the exact native command plan —
   agents (an existing one is adopted only on positive evidence it is this capability's,
   never re-created; none → stop and ask — contract), skill symlinks (the installed name → the render, per `used_by`; container
   harness → verify the `<aos_home>/personal` mount per the cheat-sheet), `uses` links (per
   row: the provider's recorded render from `aos-cap show <provider>` → each listed agent's
   skills location, under `installed_name`; a path another entry or a stranger holds →
   stop), schedules
   (`aos:<cap>:<schedule-id>`, single-owner check first), context blocks (markers), config
   keys, the capability's own tool install line — plus whatever the root MOD's household
   rules add to each agent this install creates or adopts (the `capability-lifecycle` skill's
   `reference/overlay.md`). Touch
   no harness file yet.
   Second-harness install: stage links + native plan only (the render already exists);
   schedules stay with their current owner unless the user reassigns.
9. **GATE**: show the full plan, payoff-framed — each artifact → what it does
   for the user. Wait (unless the root MOD.md says auto-accept).
10. **EXECUTE** the approved plan: commit the render in `personal/` (dated
   message — the persist hook), create the symlinks, run the native plan; `kb:`
   zones → draft grant rows into each target KB's `## Grants` table, user approves.
   A capability's tool may write machine-local files under `<aos_home>/.aos/` — kb writes
   `kb-principal.yml` (`kb init --principal` fills in a missing one, `kb config set
   principal.id=` changes it) and
   `kb-registry.yaml` (on `kb init`/`kb adopt`). Do **not** create them yourself: the tool
   owns them, the same way `aos-cap` owns the lockfile. Say they exist in the summary so
   the user is not surprised by files nobody mentioned, and leave them out of `record`
   (machine-local state is not a materialized artifact — hashing it would report drift the
   first time the tool touched it).
11. `aos-cap record <id> --version <v> --source-root <root> --artifact
    <render-file>… --link <symlink>… --uses-link <symlink>… --job <id>… --config-key <k>…`
    — `uses` links go to `--uses-link`, never `--link` (exit 19: one owner per link) — `<root>` is
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
    {{skill: upgrade}}, months from now. Hooks get the same check from the harness side:
    each one consented and active per the cheat-sheet (its doctor, where the harness has
    one) — a hook the harness skips fails silently.
13. Celebrate specifically: what, where, which schedules, degraded modes in effect.
