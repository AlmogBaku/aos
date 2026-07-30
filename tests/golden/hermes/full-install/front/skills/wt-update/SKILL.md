---
name: wt-update
description: 'Updates an existing commitment when the user reports progress: completion,
  a new deadline, a stall, or abandonment. Use when the user says "I did that", "finished
  X", "still waiting on Y", "push that to next week", "I started it", or "forget it,
  I''m not doing X". Finds the matching open action, applies the change, and routes
  any knowledge the report carries to the knowledge base. Do NOT use to file a new
  commitment (that is wt-capture) or to find time for one (wt-schedule).'
metadata:
  aos:
    origin: work-tracker@0.1.0
---
# update

Three steps. The third is the one an implementation forgets, and the one that keeps the whole
design honest.

## 1. Find what was meant

```
kb --base commitments find --where type=action --where status=next
```

The open set is small, so match by title against what the user said. Add
`--where status=waiting` when the report sounds like waiting (*"still nothing from Robin"*).

Genuinely ambiguous between two actions → ask which. Guessing here writes the wrong page and
the user finds out later, if ever, which is worse than one short question.

Nothing matches → this is probably a new commitment. Hand to `wt-capture` rather than
inventing a page here.

## 2. Apply it

`kb set` for every change — it validates against the base's schema and makes its own
attributed commit:

| The user says | Apply |
|---|---|
| *"I did that"*, *"finished X"* | `status=done` **and** `expires=<today + retention>` |
| *"I started it"* | `since=<today>` — nothing else |
| *"still waiting on Robin"* | `status=waiting waiting_on=Robin since=<today>` |
| *"push that to next week"* | the new `due=` or `block=`, and `slipped` +1 |
| *"forget it, I'm not doing X"* | `status=done` + a near `expires` — see below |

```
kb --base commitments set actions/write-the-cfp.md status=done expires=<DATE>
```

**`since` moves on any progress report**, even one that changes nothing else. That is what
keeps stall detection honest: without it the steward nags about a commitment actively being
worked on, and a nag that is wrong once gets the whole nightly report ignored.

**Completion needs `expires` as well as `status: done`.** `expires` is the only lifetime rule
kb has, so a done action without one lives forever — and a list with no exit is the graveyard
this capability exists to avoid. The retention window is an onboarding answer.

**Abandonment is a status, not a deletion.** *"Forget it"* still gets `done` plus a short
`expires`: the record of having decided not to do something is worth the few weeks it costs,
and deleting on the spot means the user cannot ask why it disappeared.

## 3. Hand the outcome to kb

*"They want a pilot in Q4"* is **knowledge**, not a commitment. It goes to the knowledge base
as a capture, so it outlives the action when `expires` fires:

```
kb capture --text "Acme wants a pilot in Q4" --source chat
```

That lands in `.kb/pending/`, and kb's archiver promotes it to the project page overnight —
you do not write the wiki page yourself.

**Without this step the never-the-only-copy rule is aspirational**, and `kb prune` starts
losing things: the action page said the call happened, the action page is gone, and what was
actually agreed went with it. Everything else here is bookkeeping; this is the part that
protects the user's memory.

A report that carries no knowledge needs nothing — most *"I did that"*s are exactly that.
Judge whether a fact came with it, and prefer capturing over not: a redundant capture costs
one queue entry, a lost one costs the thing itself.
