---
x-aos-origin: capability-lifecycle@0.1.0
name: capability-installer
description: Installs an aos capability into this harness. Use when the user says "install <capability>", offers a capability directory or CAPABILITY.md for installation, or another install needs a missing dependency installed first.
---

# capability-installer

Not in context yet? Load the `capability-lifecycle` skill first — the map, the contract,
the overlay doctrine, and the Experience rules. Then:

1. **[D]** `aos-lock manifest <dir>` → validated JSON. Validation failure → show the
   tool's error, offer fix-or-report; never improvise a parse.
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
   cheat-sheet's Secrets section) → write `<clone>/capabilities/<id>/MOD.md`.
6. **[A]** Transform per `reference/overlay.md`: original skills × MOD.md →
   personalized copies ({{mod}} slots filled, `<clone>` baked, shipped files untouched).
7. **[A]** **STAGE** per the cheat-sheet's Materialization guide: compute every
   artifact's content and the exact native command plan — agents, skills
   (`<capability>-<id>/`, `x-aos-origin` inside the frontmatter), schedules
   (`aos:<cap>:<schedule-id>`, single-owner check first), context blocks (markers),
   config keys, the capability's own tool install line. Touch nothing yet.
   Second-harness install: transform + stage only; schedules stay with their current
   owner unless the user reassigns.
8. **[D]** **GATE**: show the full plan, payoff-framed — each artifact → what it does
   for the user. Wait (unless the root MOD.md says auto-accept).
9. **[D]** **EXECUTE** the approved plan; **[A]** `kb:` zones → draft grant rows into
   each target KB's `## Grants` table, user approves.
10. **[D]** `aos-lock record <id> --version <v> --artifact <path>… --job <id>…
    --config-key <k>…` — the tool hashes and writes.
11. Celebrate specifically: what, where, which schedules, degraded modes in effect.
