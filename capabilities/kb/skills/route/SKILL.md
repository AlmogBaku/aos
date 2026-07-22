---
name: route
description: Resolves a write intent to a target knowledge base using the registry. Use when any capability captures or files content and the destination KB is not explicit — rules first, LLM only above a confidence bar, never blocking the capture.
---

# route

Resolve one write to one KB from `kb-registry.yaml`. Cost: at most one LLM call, usually
zero. Never ask the user "work or personal?" synchronously — wrong-but-cheap into a
private KB is corrected by the nightly drain.

**Candidate set**: only KBs where the writing subject holds a `route-into` grant
(`authz-check` against each KB's `## Grants` table).

Resolution order — stop at the first match:

1. **[D] Explicit tag.** User prefix ("work: …") or capability hint, matched against each
   registry entry's `tag:` or `name`. No match → it's content, not a tag.
   Record `method: explicit`.
2. **[D] Rules.** Channel binding (`routing.channels`) first, then keyword match
   (`routing.keywords`): case-insensitive substring, no stemming, no synonyms, no model
   call. Record `method: rule`.
3. **[A] LLM classification** — only if **every remaining candidate is
   `audience: private`** (shared KBs are excluded by list filter, not threshold — no path
   leads from a classifier into a shared KB, ever). One call, each candidate's `purpose`
   as rubric, returns `{kb, confidence}`. Accept iff `confidence >= confidence_bar`.
   Record `method: llm`.
4. **[D] Fallback.** Default KB's inbox, entry tagged `kb_routing: uncertain`. The
   nightly drain re-routes: into a private KB → may auto-apply (logged, reversible);
   into a shared KB → proposed to the user, never auto-applied.

Zero candidates (no grants): do not drop the payload — hand it back to the caller tagged
`kb_routing: refused`, append a `refuse` line to the default KB's `log.md` and a block to
its `_ops/needs-review.md`.

RFC-006 owns: `confidence_bar` value, tie-breaking between rules, drain-approval
batching. Not contested: shared KBs take only explicit-tagged or rule-matched writes.
