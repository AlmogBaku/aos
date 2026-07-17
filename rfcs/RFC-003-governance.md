# RFC-003: Governance & ways of working

**Status:** open · **Decides:** decision process, merge policy, cadence, commit rights

## Question

How does a small group of strong-opinion builders — each with a working private setup to defend — converge instead of bikeshedding?

## Recommendation

- **Decisions live in the repo** — RFC files for contract changes, issues for everything else. Chat is for velocity, not record.
- **Auto-accept deadlines:** every RFC carries one (default **10 days**); silence = the recommendation stands. Blocking requires a counter-proposal, not a preference.
- **A working PR outranks an RFC comment.** Evidence from a real install beats an argument about one.
- **Merge policy:** contract files (ARCHITECTURE.md, schemas, adapter interface) — 2 approvals. Capability content — 1 approval. Your own capability's non-contract files — self-merge after CI.
- **BDFL on reversible decisions:** the maintainer calls reversible things (naming details, layout, catalog ordering) without process; irreversible things (the §3 invariant, license, contract semantics) require an RFC.
- **Cadence:** async-first; a short sync only when an RFC stalls past its deadline with live disagreement.
- **Commit rights day one:** the co-design group; new contributors after one merged capability.

## Alternatives

Consensus-everything (slow death for volunteer groups) · maintainer-decides-everything (why would collaborators invest?).

## Process

This RFC bootstraps itself: comment window 10 days from publication, then the recommendation stands.
