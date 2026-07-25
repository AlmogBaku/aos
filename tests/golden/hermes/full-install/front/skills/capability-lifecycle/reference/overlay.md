# The overlay mechanism

## Contents

- Running an interview (any ONBOARDING.md)
- The transform (install and upgrade use the same one)
- Capture and fold (the overlay's write side)
- Promote and retire (the overlay's exit side)
- Persist (durability)

**MOD.md specifies what this user changed from the shipped defaults — current desired
state, not a history.** Typed answers live in its frontmatter; anything the questions
don't cover is an imperative prose statement in its body ("drain runs at 22:00, not
23:00"). The overlay family lives in the personal root at mirrored paths
(`<home>/personal/MOD.md`, `<home>/personal/capabilities/<id>/MOD.md`,
`<home>/personal/kb-registry.yaml` — §3.1); upstream never ships, writes, or merges any
of it. Everything personal is reconstructible from `original × MOD.md`; that
reconstructibility is what makes upgrades safe.

**One statement per subject — edit, never accumulate.** When something changes, find the
statement that already covers it and *rewrite* it; when it returns to the shipped
default, *delete* it; only add when nothing covers that subject yet. A MOD that says
"office hours Thursday 17:00–18:00" and later "office hours: none" is a contradiction,
not a record — the second write replaces the first, and if "none" *is* the default the
line simply goes away. History is not MOD's job: `personal/`'s git log already holds
every prior state, with dates, which is exactly why MOD doesn't carry them.

## Running an interview (any ONBOARDING.md)

1. One line of why-you're-asking, then the questions conversationally — batched, warm;
   if you can infer an answer from context, propose it instead of asking.
2. The frontmatter question list is the schema: validate each answer against its `type`
   (`string|number|boolean|enum|list|path`); enum options live in the script body.
3. `secret: true` answers: value → the harness store per the cheat-sheet's Secrets
   section; only a `{store, key}` reference lands in MOD.md.
4. Write MOD.md: typed answers in frontmatter, the user's phrasing and nuances in prose.
5. Re-runs are safe: only missing or `re_ask`-triggered questions are asked again;
   `--refresh` re-asks everything and shows a diff before writing.

## The transform (install and upgrade use the same one)

Original skills × MOD.md → the pinned render in
`personal/capabilities/<id>/skills/…` (contract: render + symlink, never copies):

- Fill `{{mod: <key>}}` slots from MOD.md frontmatter; weave the prose statements into
  the relevant instructions; leave unfilled slots intact; never edit shipped files.
- Bake `<home>/…` placeholders to the absolute household path (and `--home`/`AOS_HOME`
  into scheduled commands).
- Upgrade is the same transform with fresh upstream, written into `personal/`'s working
  tree: the current install is a drift *source*, never a merge input — and the review
  gate is a *staged, capability-scoped* diff — `git add -A -- capabilities/<id>` then
  `git diff --staged -- capabilities/<id>`, so files the re-render added are visible too
  (commit = accept, revert = rollback; the contract has the decline commands).

## Capture and fold (the overlay's write side)

When the user changes an installed capability — deliberately (via `capability-evolve`)
or by hand-editing (found by `aos-lock verify`) — the change is captured into MOD.md
*before* anything else depends on it. **Read the file first and place the change where
it belongs**: an ONBOARDING question covers it → update that frontmatter answer; a prose
statement already covers the subject → rewrite that statement; the change restores the
shipped default → remove the entry; nothing covers it yet → add one statement. Never
append a line that contradicts one already there. Then hashes are refreshed
(`aos-lock rehash`) so `verify` stays clean, and the persist hook commits. A fold is
shown to the user like any other write: "you changed X — keeping it." A fold whose edit
reaches *beyond* the `{{mod}}` slots (mechanism-shaped, not a value) is also the moment
the promotion judgment below fires.

## Promote and retire (the overlay's exit side)

Some MOD statements carry mechanism other users would want. Judgment is **signal-gated,
never reflexive** — the default fate of every evolution is the MOD, silently. It is
built on one asymmetry: a false positive costs the user's attention first (a nagging
agent drives users out — the worst outcome), then maintainer review, then permanent kit
surface; a false negative costs nothing irreversible — the statement stays in `personal/`,
promotable any day. So the bar scales with the rung, and the user's attention is priced
above everything.

**Offer signals** (no signal → no offer, ever): the evolution works around something
*objectively broken*; a *forced mechanism override* (the render was edited beyond the
`{{mod}}` slots — upstream lacks a knob; the knob's absence, never the user's value, is
what promotes); or *user-initiated* ("promote this", "others would want this").

**The tests, cheapest first:**

1. *Never-promotes list*: values of personal knobs, taste an existing knob covers,
   anything naming the user's context (people, employers, their tools). Stop here.
2. *Stranger test*: strip everything about this user — does the change still mean
   anything? Survives only with the org's context → an org candidate, never public.
3. *Ledger test*: search upstream's demand ledger —
   `gh issue list --repo <upstream> --label promotion-signal` — a match means the user
   is the second person to need this and the rule of two fires; a near-match means +1
   the existing issue rather than filing new.
4. *Explanation test*: describable in one sentence without mentioning the user.
5. For whole capabilities: dependency test (ubiquitous vs niche), the
   maintenance-willingness question ("would you respond to issues on this?"), and
   coherence (§2.5 anatomy; overlapping an existing capability routes as an evolution
   of it instead).

**The threshold ladder — take the lightest sufficient rung:** +1 an existing signal →
a new signal issue (stranger passes, no match yet) → knob/fix PR (forced override or
objectively broken, + stranger/explanation, + a matching signal OR self-evidently
universal — a real bug needs no second witness, CI is the witness) → capability PR
(all tests, ideally a prior signal). Prose rewrites ("I reworded the skill, it's
better") never go directly to PR: issue-first, and a rewrite PR needs golden-render
evidence plus a second user's confirmation. The governing principle: **one user's need
is a MOD statement; two users' need is a knob.**

**Etiquette (hard rules):** the MOD write and render always complete first; the offer
is a one-liner at the conversation's natural end, never mid-flow; once per statement, ever — a
"no" is noted on that statement ("…— not for upstream") and never re-asked; at most one promotion
offer per session, whatever qualified. And the contract's invariant: an *offer* is all
you ever do on your own — every upstream write, down to a signal issue or a +1, happens
only on the user's explicit yes.

**Promotion extracts mechanism.** The literal nuance text never ships: route to
the `capability-contribute` skill, which drafts the generic form —
a `{{mod:}}` slot + ONBOARDING question for a knob, a plain fix, or a scrubbed package —
and carries the contribution mechanics. A statement awaiting an upstream PR may carry the URL inline
("…— promoting: <url>"), which is removed when the PR lands or is dropped.

**Retirement closes the loop.** When an upgrade lands the upstream version that covers a
statement (a new interview question over the same subject, or the behavior baked in),
offer to retire it: shown as a diff, user-confirmed, written only through
`capability-evolve`. A retired statement is deleted, not annotated — it no longer
describes a difference from the default, and `personal/` git history holds what it said.

## Persist (durability)

After every MOD write and every render, commit `personal/` with a dated one-line
message ("evolve gtd-capture: drain 22:00 — <DATE>") — you do this, silently; the
user never runs git. Restore on a new machine = clone `upstream/` + clone `personal/`, then **re-install**
(the lockfile is machine-local state, not something you carry): the renders are already
there, so install re-creates the links and records a fresh lockfile. `personal/`'s only remote is private; nothing personal ever
enters any other remote.
