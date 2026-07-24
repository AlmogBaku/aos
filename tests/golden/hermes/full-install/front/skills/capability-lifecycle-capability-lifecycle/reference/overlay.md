# The overlay mechanism

**MOD.md is a ledger of personalization the agent re-applies.** Typed answers live in its
frontmatter, nuances as dated imperative prose lines in its body ("drain runs at 22:00,
not 23:00 — <DATE>"). Upstream never ships, writes, or merges any `MOD.md`
(root `~/aos/MOD.md`, per-capability `capabilities/<id>/MOD.md`, `kb-registry.yaml` —
the overlay family, §3.1). Everything personal is reconstructible from
`original × MOD.md`; that reconstructibility is what makes upgrades safe.

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

Original skills × MOD.md → personalized copies:

- Fill `{{mod: <key>}}` slots from MOD.md frontmatter; weave prose-ledger nuances into
  the relevant instructions; leave unfilled slots intact; never edit shipped files.
- Bake `<clone>/…` placeholders to the absolute clone path (and `--clone`/`AOS_CLONE`
  into scheduled commands).
- Upgrade is the same transform with fresh upstream: the current install is a drift
  *source*, never a merge input.

## Capture and fold (the ledger's write side)

When the user changes an installed capability — deliberately (via `capability-evolver`)
or by hand-editing (found by `aos-lock verify`) — the change is captured into MOD.md
*before* anything else depends on it: an existing typed answer updates the frontmatter;
anything else becomes a dated prose line. Then hashes are refreshed
(`aos-lock record`) so `verify` stays clean. A fold is shown to the user like any other
write: "you changed X — keeping it."
