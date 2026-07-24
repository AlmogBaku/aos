# nightly-drain

Run the `drain` skill over every registered KB inbox your grants cover, oldest pending
first. Close out per the skill's own close-out report section — including surfacing
`base inbox --failed` counts. `DRAIN: inbox clean.` is only the right output when
*both* pending and failed are empty; a night with failed-but-no-pending items still
gets a report, never silence.
