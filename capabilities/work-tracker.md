# Capability: work-tracker

**Tags:** usecase · **Build order:** 3 · **Seam it proves:** first vertical composing on kb + schedules; first real routing traffic; and `calendar.write` with declared degraded modes

## Scope

Commitments **only the user can keep** — captured as they speak, scheduled in the same
exchange, maintained nightly, and given an exit when they are done.

One distinction carries the whole capability, and it is not about content words:

| The user said | It is | What happens |
|---|---|---|
| *"write the CFP"* | an instruction to the agent | it writes it. Nothing is filed. |
| *"I need to find time to write the CFP"* | a commitment of theirs | filed, then scheduled |
| *"Robin says the venue is booked"* | knowledge | kb's capture path, not this |

The first two share nearly every word, which is why the judgment is *whose work is it* rather
than *does this sound like a task*. Getting it wrong in either direction is the failure mode:
file everything and the list becomes a transcript of the user's chat history; file nothing and
the capability may as well not exist.

**A list is a view, never a file.** "What's next" is `kb find --where status=next` over pages
that each carry their own state, so there is no list artifact to fall out of date. Four
statuses are the entire lifecycle — `next` · `waiting` · `someday` · `done` — where `someday`
is what keeps every passing musing out of the schedule, and `done` carrying an `expires:` is
what stops the store becoming a graveyard.

**GTD is prior art, not an implementation.** Next actions, waiting-on and someday/maybe are
useful, widely understood words and we use them. The rituals are absent: no weekly review
ceremony, no contexts, no inbox-zero discipline. A nightly steward keeps the backlog honest
instead, and its authority is bounded by one line — it adjusts its own bookkeeping silently
and **asks** before changing anything the user committed to.

**Storage is one private base**, registered as `commitments`. Not a zone in a general KB:
commitments are the user's own obligations, and `--base` matches a base's `name` and nothing
else, so the name is a contract rather than a label.

## What exists today (extraction sources — in the maintainers' live setup)

- Capture format + skill: a capture skill enforcing an entry format into a single inbox file.
- The nightly pass: an archiver-style 23:00 job over pending items.
- Scheduling: hand-run calendar blocking against working hours and sacred time.

## Depends

`capabilities: [kb, capability-lifecycle]` · `host: cron: preferred` (the nightly steward;
degraded: manual), `calendar.read`/`calendar.write: preferred` (blocking; degraded: the
commitment is filed with an estimate and no block), `messaging.inbound`/`outbound: preferred`.

Nothing is `required`: every host feature this capability wants has an honest degraded mode,
because a commitment that is merely *filed* is already worth more than one that was lost.

## Onboarding sketch

The commitments base's path, the steward's hour, working hours and sacred time (inherited from
the global MOD.md rather than re-asked), how trivial work should be treated, and whether a
block may be created without confirmation.

## v0.1 acceptance

*"I need to find time to write the CFP before Friday"* produces **both** a filed commitment
and a real calendar block **in the same exchange** — not at midnight — respecting sacred time
from the global overlay. The nightly steward touches nothing the user is waiting on, escalates
on the pattern rather than the event (three slips, not one), and is silent on a clean night.
A completed commitment sets `expires:` and leaves the store when it passes. On a harness with
no calendar, the same sentence still files the commitment and says plainly what it could not
do.

## Deliberately not built

- **A scheduled asker.** Delivery is the front agent checking `.kb/pending/` when work comes
  up in conversation — no cron, nothing materialised. The honest limit: it will not reach the
  user who never mentions work.
- **`prep`.** Assembling context before a 14:00 work block and before a 15:00 meeting is the
  same job, and most calendar entries are not commitments — folding it in here would make it
  narrower than it should be.
- **Ordered duration queries.** `--where 'estimate<5m'` compares strings, so it matches
  everything. No artifact documents an ordered `estimate` query until a duration parser exists.
