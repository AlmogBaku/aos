---
x-aos-origin: capability-lifecycle@0.1.0
name: capability-evolver
description: Changes how an installed aos capability behaves for this user and records it in their MOD.md ledger so it survives every upgrade. Use when the user asks to change an installed capability's behavior (reschedule, tone, thresholds, preferences), when verify finds hand-edit drift to capture, or when a hand-edited materialized artifact is noticed.
---

# capability-evolver

Not in context yet? Load the `capability-lifecycle` skill first. This is the ledger's
write side — the single front door for every "change this capability" ask; the classify
step routes what isn't yours.

1. **[A]** Identify the capability and artifacts (`aos-lock show <id>`); restate the
   desired change in one line.
2. **[A]** Classify:
   - an existing typed answer (an ONBOARDING question) → update the capability's MOD.md
     frontmatter;
   - a nuance → a dated imperative line in its MOD.md prose;
   - actually an upstream bug or a change for *everyone* → this is capability-builder's
     territory: its `capability-source-evolver` skill evolves the shipped source
     (building mode, approval-gated). Say so and hand over.
3. **[A]** Apply to the materialized artifact(s) per the cheat-sheet (load
   `harnesses/<harness-runtime>.md` now; native edit verbs where they exist), through
   the STAGE→GATE→EXECUTE phases.
4. **[D]** `aos-lock record <id>` — refresh the hashes so `verify` stays clean; from
   now on `capability-upgrader` re-applies this change on every upgrade.
5. Confirm: "recorded in your MOD.md — survives every upgrade."

Capture mode (drift found by `verify` or by noticing a hand-edit): same steps, but
step 3 is skipped — the change already exists; you are folding it into the ledger
(`reference/overlay.md`, "Capture and fold").
