# The overlay mechanism

**MOD.md is a ledger of personalization the agent re-applies.** Typed answers live in its
frontmatter, nuances as dated imperative prose lines in its body ("drain runs at 22:00,
not 23:00 — 2026-07-24"). The overlay family lives in the personal root at mirrored
paths (`<home>/personal/MOD.md`, `<home>/personal/capabilities/<id>/MOD.md`,
`<home>/personal/kb-registry.yaml` — §3.1); upstream never ships, writes, or merges any
of it. Everything personal is reconstructible from `original × MOD.md`; that
reconstructibility is what makes upgrades safe.

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

- Fill `{{mod: <key>}}` slots from MOD.md frontmatter; weave prose-ledger nuances into
  the relevant instructions; leave unfilled slots intact; never edit shipped files.
- Bake `<home>/…` placeholders to the absolute household path (and `--home`/`AOS_HOME`
  into scheduled commands).
- Upgrade is the same transform with fresh upstream, written into `personal/`'s working
  tree: the current install is a drift *source*, never a merge input — and the review
  gate is a *staged, capability-scoped* diff — `git add -A -- capabilities/<id>` then
  `git diff --staged -- capabilities/<id>`, so files the re-render added are visible too
  (commit = accept, revert = rollback; the contract has the decline commands).

## Capture and fold (the ledger's write side)

When the user changes an installed capability — deliberately (via `capability-evolver`)
or by hand-editing (found by `aos-lock verify`) — the change is captured into MOD.md
*before* anything else depends on it: an existing typed answer updates the frontmatter;
anything else becomes a dated prose line. Then hashes are refreshed
(`aos-lock rehash`) so `verify` stays clean, and the persist hook commits. A fold is
shown to the user like any other write: "you changed X — keeping it." A fold whose edit
reaches *beyond* the `{{mod}}` slots (mechanism-shaped, not a value) is also the moment
the promotion judgment below fires.

## Promote and retire (the ledger's exit side)

Some ledger lines carry mechanism other users would want. Judgment is **signal-gated,
never reflexive** — the default fate of every evolution is the MOD, silently. It is
built on one asymmetry: a false positive costs the user's attention first (a nagging
agent drives users out — the worst outcome), then maintainer review, then permanent kit
surface; a false negative costs nothing irreversible — the line stays in `personal/`,
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
is a MOD line; two users' need is a knob.**

**Etiquette (hard rules):** the MOD write and render always complete first; the offer
is a one-liner at the conversation's natural end, never mid-flow; once per ledger line,
ever — a "no" is recorded as a dated line and never re-asked; at most one promotion
offer per session, whatever qualified. And the contract's invariant: an *offer* is all
you ever do on your own — every upstream write, down to a signal issue or a +1, happens
only on the user's explicit yes.

**Promotion extracts mechanism.** The literal nuance text never ships: route to
capability-builder's `capability-source-evolver` skill, which drafts the generic form —
a `{{mod:}}` slot + ONBOARDING question for a knob, a plain fix, or a scrubbed package —
and carries the contribution mechanics. A promotion-pending line may carry its PR URL
("promoted: <url> — 2026-07-25").

**Retirement closes the loop.** When an upgrade lands the upstream version that covers a
line (a new interview question over the same subject, or the behavior baked in), offer
to retire it: shown as a diff, user-confirmed, written only through `capability-evolver`.
A retired line is deleted, not archived — `personal/` git history is the archive.

## Persist (the ledger's durability)

After every ledger write and every render, commit `personal/` with a dated one-line
message ("evolve gtd-capture: drain 22:00 — 2026-07-25") — you do this, silently; the
user never runs git. Restore on a new machine = clone `upstream/` + clone `personal/`, then **re-install**
(the lockfile is machine-local state, not something you carry): the renders are already
there, so install re-creates the links and records a fresh lockfile. `personal/`'s only remote is private; nothing personal ever
enters any other remote.
