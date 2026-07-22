---
name: route
description: Resolves a write intent to a target knowledge base using the registry. Use when any capability captures or files content and the destination KB is not explicit — rules first, LLM only above a confidence bar, never blocking the capture.
---

# route

You are resolving one write (usually a capture) to one KB from `kb-registry.yaml`.
**Capture latency is sacred**: cost is at most one cheap LLM call, usually zero, and you
never ask the user "work or personal?" synchronously. Wrong-but-cheap beats slow-but-sure —
misroutes into private KBs are corrected asynchronously by the nightly drain.

## Candidate set (authorization shapes routing)

Before anything: the candidate KBs are only those the writing subject holds a `route-into`
grant for (check with the `authz-check` skill against each KB's `## Grants` table). No
grant, not a candidate.

## Resolution order — stop at the first match

1. **[D] Explicit tag wins.** A user prefix ("work: …") or a capability-supplied hint names
   the KB directly. Record `method: explicit`.
2. **[D] Deterministic rules.** First channel/agent binding (`routing.channels` in the
   registry — the channel the capture arrived on), then keyword/entity match
   (`routing.keywords`). String matching only, no model call. Record `method: rule`.
3. **[A] LLM classification** — allowed **only if every remaining candidate is
   `audience: private`**. Shared KBs are excluded from this step by a list filter, not a
   threshold: no path leads from a classifier into a shared KB, ever (§4.2 normative).
   One cheap call using each candidate's `purpose` field as the rubric, returning
   `{kb, confidence}`. Accept iff `confidence >= confidence_bar` from the registry.
   Record `method: llm`.
4. **[D] Fallback.** Write to the **default KB's inbox**, tagged in the entry with
   `kb_routing: uncertain`. The nightly drain re-routes with review: moves into a private
   KB may auto-apply (logged, reversible); moves into a shared KB are **proposed to the
   user, never auto-applied**.

## Deferred to RFC-006

The `confidence_bar` value (registry default 0.7), tie-breaking when two rules match, and
how drain re-route approvals are batched are contested — follow the registry values and
current spec text, and expect them to change with RFC-006's replay evidence. What is NOT
contested and never changes without a spec amendment: shared KBs take only explicit-tagged
or rule-matched writes.

## On refusal

If authorization leaves zero candidates, do not drop the payload: hand it back to the
caller for the default inbox with `kb_routing: refused`, and append a `refuse` line to the
default KB's `log.md` plus a block to `_ops/needs-review.md` (data is preserved; latency is
preserved; a human decides later).
