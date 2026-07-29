# Dogfood checklist (later, explicitly user-approved sessions)

Items the build phase deliberately does NOT automate. Each is a separate session the user
starts on purpose; none runs from CI or from an implementation agent's own initiative.

- [ ] **Real personal install**: bootstrap per `BOOTSTRAP.md` (capability-lifecycle first — its
      own interview is the global one — then kb) on the live Hermes with the
      user's own answers (not fixtures) — capability-lifecycle + kb + work-tracker.
- [ ] **`kb adopt` report on the production KB** — report-only; nothing committed, nothing rewritten.
- [ ] **2-week live routing replay** — hand-labeled real captures vs router decisions;
      misroute rate < 5% (ARCHITECTURE Appendix B #2). Evidence feeds RFC-006.
- [ ] **RFC-005 evidence**: run private-fork vs gitignored+backup overlay persistence side by side;
      count incidents.
- [ ] Next live render: verify no literal `<home>` survives in *transformed*
  capabilities' materialized copies (one bake miss shipped in the 2026-07-24 goldens —
  kb entry skill); add a forbid-sentinel to expectations with that render
- [ ] Full **removal** after any dogfood install that isn't kept (cheatsheet Removal section);
      `doctor`-style check that nothing is orphaned.
- [ ] **Live base migration** — run the `kb-import` skill on the production KB (survey →
      agreement → sample → batches; source read-only; the state conversation seeds the
      real attention window). The skill exists for exactly this session.
- [ ] **State cap + eviction tuning**: dogfood `state.max_items` (default 20) and the
      42-day staleness window against real attention churn.
- [ ] **A month of a real two-person base** (RFC-010 Q1's own decision method): per-principal
      curation, `kb lint` run by hand or by each member's automation, counting what the
      pending queue actually accumulates and what a human had to fix. If per-principal
      curation keeps the queue drainable, CI curation is unnecessary rather than deferred.
- [ ] **`kb config set`'s missing grant row** — decide it rather than carrying it: the fix
      needs a push to `aos-kb-template`, so it is a decision (see the BUILD-GAPS row). Until
      then every base whose schema was edited carries one permanent audit critical.
- [ ] **Commitment tracking against real commitments** — the thing work-tracker exists for,
      and the only way to find out whether the speech-act split holds outside fixtures: does
      *"I need to find time to…"* fire reliably, and does *"write the CFP"* stay silent?
