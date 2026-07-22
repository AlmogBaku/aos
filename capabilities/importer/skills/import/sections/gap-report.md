# GAP.md — what didn't map

One section per finding, ordered by how much they'd hurt a second user:

```markdown
## <kind>: <one line>
**Where:** <artifact / path>
**What:** <the thing that didn't map — hardcoded path, harness-only API, inline secret
(flagged, not copied), unclear mechanism-vs-nuance call, dropped harness tuning>
**Draft handling:** <what the draft does meanwhile — placeholder, {{mod}} slot, omitted>
**Proposed fix:** <spec change, cheat-sheet addition, or "author decision needed">
```

Kinds worth calling out explicitly: `secret` (name + where it lived, never the value),
`hardcoded-path`, `harness-only` (no neutral primitive exists — candidate evidence for
the §5.2 vocabulary or the §2.4 plugins route), `judgment` (split calls you weren't sure
of), `drift` (live artifacts that contradict each other).

GAP.md is the importer's real product as much as the skeleton: each entry either becomes
a spec fix (via the ledger) or documents an honest limit of the contract.
