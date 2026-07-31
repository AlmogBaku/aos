---
name: capture
description: "Records something the user has said they must do themselves: classifies the commitment as next, waiting, someday or trivial, writes it as an action page in their commitments base, and hands off to wt-schedule when it needs real hours. Use when the user commits to work of their own — \"I need to find time to…\", \"I have to…\", \"remind me to…\", \"help me remember…\", \"put that on my list\", \"I should … at some point\". Do NOT use when the user asks the assistant to do the work (\"write the CFP\", \"research X\", \"email Sam\") — that is a request to act now, not a commitment to track. Do NOT use for thoughts, facts or notes carrying no commitment; those are knowledge and belong to kb-capture."
---

# capture

Write the page, confirm, hand off. Under five seconds to the confirmation.

## Clarify — one question, asked of yourself

**Is this mine to do?** Not *"is it actionable?"* — everything is actionable to an agent, so
that question routes every request into the list.

| The commitment is | status: | plus | then |
|---|---|---|---|
| real work of the user's | `next` | — | hand off to {{skill: schedule}} |
| someone else's to answer | `waiting` | `waiting_on:` | nothing more |
| a deadline, not hours | `next` | `due:` | a reminder, no block |
| not now, maybe never | `someday` | — | nothing more |
| trivial | `next` | `estimate:` | say *"that's a two-minute job — worth doing now?"* **and file it anyway** |

**`status` is one of exactly those four words.** Nothing validates it, so a fifth value —
`trivial`, `blocked`, `urgent` — is written happily and then matches none of the steward's
queries nor its `--without block` backstop, which makes the commitment permanently invisible.
Trivial work is `next` with a small `estimate:`, not a status of its own.

`someday` protects the list: without it every musing becomes a scheduled commitment, and a
schedule the user stops trusting is worse than none.

**Never block on the recommendation.** Ask about the two-minute job in the same breath as
confirming, not instead of it — a commitment lost to a clarifying question costs more than a
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
created: 2026-07-29            # required
timestamp: 2026-07-29T14:32    # required
status: next                   # plus due / estimate / waiting_on per the table above
since: 2026-07-29
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

Needs real hours → invoke {{skill: schedule}}, in a sub-agent where the harness has them and inline
otherwise. Say which you did, because *"blocked 14:00–16:00 tomorrow"* and *"filed, no
calendar here"* are different promises and the user is entitled to know which one they got.

The user should experience one act, not two. {{skill: schedule}} comes back with the time; you
confirm once, with the time in it.

**How the confirmation reads is the user's call**: {{mod: action_format}}. Some people want the
commitment phrased back in full, some want one emoji and nothing else. Honour it exactly —
this is the line they see several times a day, and it is the whole surface of an interaction
whose other half is silent.

## When something fails

The commitment matters more than the bookkeeping around it. If the page landed and the
attribution, the flag or the hand-off did not, mention it and move on — an unscheduled action
is one without a `block`, which the steward's `--without block` backstop already finds. Losing
the thought is the only real failure here.
