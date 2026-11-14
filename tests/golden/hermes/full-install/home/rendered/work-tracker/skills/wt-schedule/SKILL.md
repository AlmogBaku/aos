---
name: wt-schedule
description: Estimates a commitment, links it to its project, and blocks time for
  it on the user's calendar. Use when the user asks to find time for something — "when
  can I do this?", "find me two hours for the CFP", "block time for that tomorrow",
  "I want to work on it today" — and immediately after wt-capture files a commitment
  that needs real hours. Do NOT use for a commitment that needs only a deadline or
  a reminder, and do NOT use to change what the user committed to — that is wt-update.
metadata:
  aos:
    origin: work-tracker@0.1.5
---
# schedule

Find real time for a commitment and write it down. This runs **when the user speaks**, not
overnight — *"I want to work on the CFP tomorrow"* is worthless if the block appears at
midnight.

## 1. Estimate

How long is this, honestly? Prefer the user's own number where they gave one; otherwise a
rough estimate beats none, because it decides how much calendar to look for and lets the
steward spot a two-minute job that has sat for three weeks.

Record it as `estimate:` on the action — `30m`, `1h30m`, `2h`. The user's granularity is
half hours: round to the nearest 30 minutes; invented precision (`37m`, `45m`) reads as noise.

## 2. Read the calendar before proposing anything

Existing blocks, meetings, and the working windows from the global `MOD.md`. Then the rules
that come from the user, not from this skill:

- **Working hours** bound where a block may land at all: 9:00–18:00 weekdays, Europe/Lisbon,
  with quiet Fridays. Mornings are deep work — nothing interactive before noon.
- **Blocks go on the user's personal calendar** — not a work one, where they would be
  visible to the wrong people.
- **Sacred time is never scheduled over, and never silently moved.** For this user that is
  choir practice, Thursdays 19:00–21:00 — never book work there. This skill writes to a
  real calendar, so that rule is what makes the capability trustworthy rather than something
  the user has to check up on. A conflict gets surfaced — *"the only two-hour gap is during
  choir practice; shall I look at Friday instead?"* — with the next free window offered,
  never resolved on their behalf.

The global `MOD.md`'s red lines apply here too. Sending an invitation to another person is
acting outward as the user; blocking time on their own calendar is not.

## 3. Take the slot and write it

wt-capture hands you the page path. Reached directly (*"find me two hours for the CFP"*),
find it first rather than guessing at the slug — the open set is small:

```
kb --base commitments find --where type=action --where status=next
kb --base commitments set actions/write-the-cfp.md block=<TIMESTAMP> estimate=45m
```

`kb set` validates every key against the base's schema and makes its own attributed commit,
so nothing else is needed. Both fields are declared at install — an undeclared one exits 14
rather than writing a page lint would later flag.

Link the action to its project in the same pass where one exists. **The outer quotes are
load-bearing** — `kb set` runs each value through a YAML parser, so a bare `[[…]]` is read as
a nested list and stored as one, silently and with exit 0:

```
kb --base commitments set actions/write-the-cfp.md 'project="[[projects/booking-deal]]"'
```

That link is what lets the steward answer *"what is this for"* without reading the body — via
`kb find --where 'project=[[projects/booking-deal]]'`, since `kb links` reads body text only
and never frontmatter.

## 4. Report the slot back

Hand the actual time back to wt-capture (or, reached directly, to the conversation) —
*"blocked 14:00–15:00 Tuesday"*. Reached through wt-capture, the user-facing confirmation is
still the user's single 🦜 and nothing else; reached directly (*"find me two hours"*), they
asked for a time, so name it.

## Where this runs

Where the harness can spawn a sub-agent, run in one. Not for latency — taking ten seconds to
find a good slot is fine, even reassuring — but because finding one means reading the
calendar, the existing blocks and the project page, none of which the conversation needs in
its context afterwards.

Inline is a correct fallback, not a failure. Say which one happened.

## Without a calendar

Say so plainly, once — when the user asked for time directly; under wt-capture the user's
🦜-only confirmation holds and the missing block is what the steward's backstop reports: actions, statuses, deadlines and the steward all still work; there are
no blocks. Then set `estimate:` anyway and leave `block` absent — the steward's
`--without block` backstop is exactly the query that finds these, so a commitment with no
calendar is tracked rather than lost. Silently doing nothing is the one unacceptable
outcome, because the user believes time was found.
