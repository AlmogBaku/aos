---
name: capability-evolver
description: Changes how an installed aos capability behaves for this user and records it in their MOD.md ledger so it survives every upgrade. Use when the user asks to change an installed capability's behavior (reschedule, tone, thresholds, preferences), asks to promote a tweak upstream or says a change should be for everyone, when verify finds hand-edit drift to capture, or when a hand-edited rendered artifact is noticed.
---

# capability-evolver

Not in context yet? Load the `capability-lifecycle` skill first — the map, the
contract, the overlay doctrine, and the Experience rules. This is the ledger's
write side — the single front door for every "change this capability" ask; the classify
step routes what isn't yours. **Default fate of every change: the user's MOD, silently.**

1. **[A]** Identify the capability and artifacts (`aos-lock show <id>`); restate the
   desired change in one line.
2. **[A]** Classify:
   - an existing typed answer (an ONBOARDING question) → update the capability's MOD.md
     frontmatter;
   - a nuance → a dated imperative line in its MOD.md prose;
   - actually an upstream bug or explicitly for *everyone* → this is capability-builder's
     territory: its `capability-source-evolver` skill evolves the shipped source
     (building mode, approval-gated). Say so and hand over — nothing lands in MOD.
3. **[A]** Write the MOD.md change **first** (`reference/overlay.md`, Capture and fold —
   the ledger lands before anything depends on it), then apply to the pinned render in `personal/capabilities/<id>/` (and any native
   artifacts per the cheat-sheet — load `harnesses/<harness-runtime>.md` now; native
   edit verbs where they exist), through the STAGE→GATE→EXECUTE phases.
4. **[D]** `aos-lock rehash <id>` — refresh the recorded hashes in place so `verify`
   stays clean; the persist hook commits `personal/` (dated message). From now on
   `capability-upgrader` re-applies this change on every upgrade. (New artifacts, jobs,
   or keys → a full `aos-lock record` with the complete set from `aos-lock show`.)
5. Confirm: "recorded in your MOD.md — survives every upgrade."
6. **[A]** Promotion check — **signal-gated, never reflexive** (the judgment, tests,
   threshold ladder, and etiquette live in `reference/overlay.md`, Promote and retire).
   An offer fires only on: objectively-broken workaround · forced mechanism override
   (the change fought the template beyond its `{{mod}}` slots) · the user asked.
   At most one one-liner offer, at the conversation's end, once per ledger line ever;
   a "no" is recorded and never re-asked. Yes → hand to `capability-source-evolver`
   with the ledger line. **Never open a PR or file an issue yourself — every upstream
   write needs the user's explicit yes (contract).**

Capture mode (drift found by `verify` or by noticing a hand-edit): same steps, but
step 3 is skipped — the change already exists; you are folding it into the ledger
(`reference/overlay.md`, "Capture and fold").
