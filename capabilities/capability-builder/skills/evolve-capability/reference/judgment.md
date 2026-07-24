# Small vs. major — worked examples

**Small** (apply directly — note *where* each one lives):
- "The drainer's cron should run at 22:30, not 23:00" — a personalization answer
  (`drain_hour`): update it through the onboarding skill, then sync the live cron to
  match. The schedule's existence didn't change, only its answer.
- "Capture entries should keep the raw timestamp" — a wording/format tweak inside an
  existing skill's reference doc. gtd-capture is upstream-shipped, so this is NOT a
  silent clone edit: personalizable → the overlay; otherwise draft the change and
  offer an upstream PR (local divergence only if the user knowingly accepts it).
  For a capability the user authored, the same tweak is just a clone edit.
- "Turn off the Friday digest" — a personalization answer changing: onboarding
  updates it, the live artifact syncs.

**Major** (re-run the scaled procedure):
- "The drainer should also post a weekly summary to Slack" — a new schedule, a new
  `depends.host` need (`messaging.outbound`).
- "Split capture into two skills, one for quick notes and one for tasks" — changes the
  skill boundary, changes what the entry skill's map covers.
- "kb should also accept voice notes" — a new `depends.host` primitive
  (`voice.stt`), changes what the capability is responsible for.

The line: does anything get created, deleted, or change what it's scoped to own? If
yes, major — regardless of how small the request sounded.
