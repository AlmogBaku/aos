# Small vs. major — worked examples

**Small** (apply directly — note *where* each one lives):
- "The steward's cron should run at 22:30, not 23:00" — a personalization answer
  (`steward_hour`): update it through the `capability-onboard` skill, then sync the live cron to
  match. The schedule's existence didn't change, only its answer.
- "Capture entries should keep the raw timestamp" — a wording/format tweak inside an
  existing skill's reference doc. work-tracker is upstream-shipped, so this is NOT a
  silent source edit: personalizable → the overlay; otherwise draft the change on a
  branch and offer the contribution (the mechanics the `capability-contribute` skill
  links; local divergence only if the user knowingly accepts it). For a capability the user authored, the same
  tweak is a direct `personal/` edit.
- "Turn off the Friday digest" — a personalization answer changing: onboarding
  updates it, the live render syncs.
- **A knob promotion** — the evolver hands over the MOD statement "captures after 22:00
  default to personal": upstream's capture skill hardcodes no such
  cutoff, and the user fought the template (mechanism override). The promotion is a
  `{{mod: late_capture_kb}}` slot at that step + an ONBOARDING question ("where do
  late-night captures default?") + a MOD.example placeholder — never the user's KB
  names. Small: nothing new is owned; the ledger search the skill describes decides
  issue vs PR.

**Major** (re-run the scaled procedure):
- "The steward should also post a weekly summary to Slack" — a new schedule, a new
  `depends.host` need (`messaging.outbound`). As a *promotion* ("promote my weekly-
  summary hack") it is still major: the scaled procedure runs before any contribution
  is drafted, and the maintenance-willingness question applies (the overlay doctrine's
  judgment — would the user respond to issues on it?).
- "Split capture into two skills, one for quick notes and one for tasks" — changes the
  skill boundary, changes what the entry skill's map covers.
- "kb should also accept voice notes" — a new `depends.host` primitive
  (`voice.stt`), changes what the capability is responsible for.

The line: does anything get created, deleted, or change what it's scoped to own? If
yes, major — regardless of how small the request sounded.
