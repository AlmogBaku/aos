# Dogfood checklist (later, explicitly user-approved sessions)

Items the build phase deliberately does NOT automate. Each is a separate session the user
starts on purpose; none runs from CI or from an implementation agent's own initiative.

- [ ] **Real personal install**: bootstrap per `docs/BOOTSTRAP.md` on the live Hermes with the
      user's own answers (not fixtures) — kb + onboarding + gtd-capture.
- [ ] **`kb adopt` report on the production KB** — report-only; nothing committed, nothing rewritten.
- [ ] **2-week live routing replay** — hand-labeled real captures vs router decisions;
      misroute rate < 5% (ARCHITECTURE Appendix B #2). Evidence feeds RFC-006.
- [ ] **RFC-005 evidence**: run private-fork vs gitignored+backup overlay persistence side by side;
      count incidents.
- [ ] Full **removal** after any dogfood install that isn't kept (cheatsheet Removal section);
      `doctor`-style check that nothing is orphaned.
