---
name: capability-evolve
description: Changes how an installed aos capability behaves for THIS user and records
  it in their MOD.md so it survives every upgrade. Use when the user asks to reschedule,
  retune, retone or otherwise adjust an installed capability ("make the steward run
  at 22:00", a threshold, a preference), when they say a tweak should be for everyone,
  or when a hand-edited render needs capturing back. Do NOT use to change the shipped
  source for all users — it classifies that and hands it to capability-contribute
  — and not to install, upgrade or remove, which are their own skills.
metadata:
  aos:
    origin: capability-lifecycle@0.3.4
---
# capability-evolve

Not in context yet? Load the `capability-lifecycle` skill first — the map, the
contract, the overlay doctrine, and the Experience rules. This is the overlay's
write side — the single front door for every "change this capability" ask; the classify
step routes what isn't yours. **Default fate of every change: the user's MOD, silently.**
MOD states current desired state, so every write is an *edit in place*, never an
appended record (the `capability-lifecycle` skill's `reference/overlay.md`).

1. **[A]** Identify the capability and artifacts (`aos-lock show <id>`); restate the
   desired change in one line.
2. **[A]** **Read the current MOD.md first**, then classify (if the change adds or moves a
   skill's files, `capability-lifecycle`'s `reference/naming.md` binds the names and where
   references may point):
   - an ONBOARDING question covers it → update that typed answer in the frontmatter;
   - a prose statement already covers the subject → rewrite that statement (never add a
     second one that contradicts it — "office hours: none" replaces "office hours
     Thursday 17:00–18:00", it does not follow it);
   - the change restores the shipped default → delete the entry; MOD only states
     differences;
   - nothing covers the subject yet → add one imperative statement;
   - actually an upstream bug or explicitly for *everyone* → the `capability-contribute`
     skill owns it: it changes the shipped source (building mode, approval-gated). Say so
     and hand over — nothing lands in MOD.
3. **[A]** Write the MOD.md change **first** (the `capability-lifecycle` skill's
   `reference/overlay.md`, Capture and fold —
   the MOD statement lands before anything depends on it), then apply to the pinned render in `personal/capabilities/<id>/` (and any native
   artifacts per the cheat-sheet — the `capability-lifecycle` skill's
   `reference/harness-<harness-runtime>.md`, load it now; native
   edit verbs where they exist), through the STAGE→GATE→EXECUTE phases.
4. **[D]** `aos-lock rehash <id>` — refresh the recorded hashes in place so `verify`
   stays clean; the persist hook commits `personal/` (dated message). From now on
   `capability-upgrade` re-applies this change on every upgrade. (New artifacts, jobs,
   or keys → a full `aos-lock record` with the complete set from `aos-lock show`.)
5. Confirm: "recorded in your MOD.md — survives every upgrade."
6. **[A]** Promotion check — **signal-gated, never reflexive** (the judgment, tests,
   threshold ladder, and etiquette live in the `capability-lifecycle` skill's
   `reference/overlay.md`, Promote and retire).
   An offer fires only on: objectively-broken workaround · forced mechanism override
   (the change fought the template beyond its `{{mod}}` slots) · the user asked.
   At most one one-liner offer, at the conversation's end, once per statement ever;
   a "no" is recorded and never re-asked. Yes → hand to `capability-contribute`
   with the statement. **Never open a PR or file an issue yourself — every upstream
   write needs the user's explicit yes (contract).**

Capture mode (drift found by `verify` or by noticing a hand-edit): same steps, but step 3's
**second half** is skipped — the render already carries the change, so there is nothing to apply.
**Step 3's MOD.md write still happens, and it is the whole point of capture mode**: the edit
exists on disk and nowhere in the overlay, so the next upgrade would silently drop it. Skip the
write and step 5's "recorded in your MOD.md — survives every upgrade" is a lie
(the `capability-lifecycle` skill's `reference/overlay.md`, "Capture and fold").
