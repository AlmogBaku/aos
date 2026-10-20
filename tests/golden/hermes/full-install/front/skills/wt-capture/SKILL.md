---
name: wt-capture
description: 'Records something the user has said they must do themselves: classifies
  the commitment as next, waiting, someday or trivial, writes it as an action page
  in their commitments base, and hands off to wt-schedule when it needs real hours.
  Use when the user commits to work of their own — "I need to find time to…", "I have
  to…", "remind me to…", "help me remember…", "put that on my list", "I should … at
  some point". Do NOT use when the user asks the assistant to do the work ("write
  the CFP", "research X", "email Sam") — that is a request to act now, not a commitment
  to track. Do NOT use for thoughts, facts or notes carrying no commitment; those
  are knowledge and belong to kb-capture.'
metadata:
  aos:
    origin: work-tracker@0.1.4
---
# capture

Write the page, confirm, hand off. Under five seconds to the confirmation.

## Clarify — one question, asked of yourself

**Is this mine to do?** Not *"is it actionable?"* — everything is actionable to an agent, so
that question routes every request into the list.

| The commitment is | status: | plus | then |
|---|---|---|---|
| real work of the user's | `next` | — | hand off to wt-schedule |
| someone else's to answer | `waiting` | `waiting_on:` | nothing more |
| a deadline, not hours | `next` | `due:` | a reminder, no block |
| not now, maybe never | `someday` | — | nothing more |
| trivial | `next` | `estimate:` | **file it anyway**; the confirmation is still only 🦜 (see below) |

**`status` is one of exactly those four words.** Nothing validates it, so a fifth value —
`trivial`, `blocked`, `urgent` — is written happily and then matches none of the steward's
queries nor its `--without block` backstop, which makes the commitment permanently invisible.
Trivial work is `next` with a small `estimate:`, not a status of its own.

`someday` protects the list: without it every musing becomes a scheduled commitment, and a
schedule the user stops trusting is worse than none.

**Never block on a recommendation.** This user's confirmation is a bare 🦜, so there is no
two-minute-job question at all — a commitment lost to a clarifying question costs more than a
wrong estimate. If the exchange resolves it (*"yeah, done"*), file it `done` with an
`expires:` rather than skipping the page.

## Write it

The page is `actions/<slug>.md`, and there is no `kb` verb that creates one — write it with
ordinary file tools, then attribute it:

```
kb --base commitments commit --verb create --path actions/write-the-cfp.md \
  --summary "commitment: write the KubeCon CFP"
```

All three flags are required. Skip this and the page reaches git only through the sync sweep,
with no acting subject, and `kb lint` reports it — as a *report*, not a failure: bare `kb lint`
exits 0 even with criticals in it, so read what it says rather than trusting the exit code.

Frontmatter. The four marked `required` are the ones `kb lint` reports as missing — write all
seven anyway, since the steward's queries depend on `status` and `since`:

```yaml
title: call the dentist        # required
type: action                   # required
created: <DATE>            # required
timestamp: <TIMESTAMP>    # required
status: next                   # plus due / estimate / waiting_on per the table above
since: <DATE>
slipped: 0
```

**The user's own words go in the body, verbatim** — that sentence is the only record of what
they actually committed to, and a tidier paraphrase is usually a paraphrase of what you
assumed they meant.

Then add the page to `index.md`, or it is invisible to the map even though every query still
finds it: `kb --base commitments index rebuild` does it mechanically.

Shape and the full field list: the `work-tracker` skill's `reference/action-page.md`.

A correction to something already filed is `kb capture --corrects <path>` — a link, not prose
for a later pass to guess at.

## Hand off

Needs real hours → invoke wt-schedule, in a sub-agent where the harness has them and inline
otherwise. Which one happened is not part of the confirmation for this user.

The user should experience one act, not two. wt-schedule comes back with the time (or with
"no calendar"); you confirm once, with 🦜 and nothing else. The block is on their calendar for
them to see. The only extra words ever allowed: wt-schedule's one-time *"no calendar here"*
notice the very first time it happens, and a scheduling conflict with sacred time, which must
be surfaced rather than resolved (wt-schedule).

**How the confirmation reads is the user's call**: confirm every commitment with a single 🦜
emoji — nothing else, ever. Never echo the commitment back: no restated title, no slot time,
no "filed", no two-minute-job remark, no note about sub-agent vs inline. The 🦜 is the whole
reply, including after a wt-schedule hand-off. Honour it exactly — this is the line they see
several times a day, and it is the whole surface of an interaction whose other half is silent.
(The one exception is a failure the user must know about — see below — never a success.)

**Phrasing on the page is verb-first** (*"Email Sam the deck"*, not *"Sam has the deck"*) —
that is the `title:` and anything a list view shows. Anything with a deadline gets the
deadline in the phrasing (*"Submit the KubeCon CFP by Fri 24 Oct"*), because that is the part
worth seeing at a glance. The body still holds the user's own words verbatim.

## When something fails

The commitment matters more than the bookkeeping around it. If the page landed and the
attribution, the flag or the hand-off did not, mention it and move on — an unscheduled action
is one without a `block`, which the steward's `--without block` backstop already finds. Losing
the thought is the only real failure here.
