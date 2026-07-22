# nightly-drain

Run the `drain` skill over every registered KB inbox your grants cover, oldest entries
first. Follow it exactly: triage to next-actions and reminders, apply corrections, mark
`#triaged`, never delete lines (the archiver's later promote pass owns removal). If there
is nothing untriaged, output exactly `DRAIN: inbox clean.` and deliver nothing.
