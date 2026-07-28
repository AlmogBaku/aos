---
name: capture
description: "Records something the user has said they must do themselves: classifies the commitment as next, waiting, someday or trivial, writes it as an action page in their commitments base, and hands off to wt-schedule when it needs real hours. Use when the user commits to work of their own — \"I need to find time to…\", \"I have to…\", \"remind me to…\", \"help me remember…\", \"put that on my list\", \"I should … at some point\". Do NOT use when the user asks the assistant to do the work (\"write the CFP\", \"research X\", \"email Sam\") — that is a request to act now, not a commitment to track. Do NOT use for thoughts, facts or notes carrying no commitment; those are knowledge and belong to kb-capture."
---

# capture

Write the page, confirm, hand off. Under five seconds to the confirmation.

## Clarify — one question, asked of yourself

**Is this mine to do?** Not *"is it actionable?"* — everything is actionable to an agent, so
that question routes every request into the list.

| The commitment is | status | then |
|---|---|---|
| real work of the user's | `next` | hand off to `wt-schedule` |
| someone else's to answer | `waiting` + `waiting_on:` | nothing more |
| a deadline, not hours | `next` + `due:` | a reminder, no block |
| not now, maybe never | `someday` | nothing more |
| trivial | `next` + `estimate:` | say *"that's a two-minute job — worth doing now?"* **and file it anyway** |

`someday` is what protects the list. Without it every musing becomes a scheduled commitment,
and a schedule you stop trusting is worse than none.

**Never block on the recommendation.** Ask about the two-minute job in the same breath as
confirming, not instead of it — a commitment lost to a clarifying question is worse than one
filed with a wrong estimate. If the exchange resolves it (*"yeah, done"*), file it `done`
with an `expires:` rather than deleting the page: the record of having done it is worth the
one line.

## Write it

The page is `actions/<slug>.md`, and there is no `kb` verb that creates one — write it with
ordinary file tools, then attribute it:

```
kb --base commitments commit --verb create --path actions/write-the-cfp.md \
  --summary "commitment: write the KubeCon CFP"
```

All three flags are required. Skip this and the page reaches git only through the sync
sweep, with no acting subject, and `kb lint` reports it.

Frontmatter: `type: action`, `status:`, `since: <today>`, `slipped: 0`, plus `due`/`estimate`/
`waiting_on` as the table above dictates. **The user's own words go in the body, verbatim** —
that sentence is the only record of what they actually committed to, and a tidier paraphrase
is usually a paraphrase of what you assumed they meant.

Shape and the full field list: the `work-tracker` skill's `reference/action-page.md`.

A correction to something already filed is `kb capture --corrects <path>` — a link, not prose
for a later pass to guess at.

## Hand off

Needs real hours → invoke `wt-schedule`, in a sub-agent where the harness has them and inline
otherwise. Say which you did, because *"blocked 14:00–16:00 tomorrow"* and *"filed, no
calendar here"* are different promises and the user is entitled to know which one they got.

The user should experience one act, not two. `wt-schedule` comes back with the slot; you
confirm once, with the slot in it.

## When something fails

The commitment matters more than the bookkeeping around it. If the page landed and the
attribution, the flag or the hand-off did not, mention it and move on — an unscheduled action
is one without a `block`, which the steward's `--without block` backstop already finds. Losing
the thought is the only real failure here.
