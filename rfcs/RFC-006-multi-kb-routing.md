# RFC-006: Multi-KB routing & authorization model

**Status:** open · **Decides:** whether ARCHITECTURE §4.2–4.3 holds as specced · **Capability:** [kb](../capabilities/kb.md) (contested core; its extraction plan is unaffected)

## Question

The spec takes a firm position: routing is rules-first (explicit tag → channel/keyword rules → LLM only above a confidence bar), uncertain items land in the default KB's inbox for nightly re-route, and **shared-audience KBs never accept LLM-routed writes** — the classifier may only choose among private KBs. Authorization is one vocabulary (subjects × objects × verbs) shared with the permission gate (RFC-007).

This is the highest-stakes judgment call in the kit: a misroute across a privacy boundary (personal → team KB) is trust-terminating, but over-restricting routing makes multi-KB capture annoying enough that people fall back to one KB.

## Options

1. **As specced (recommended):** the §4.2–4.3 hybrid. Wrong-but-cheap inside private space, deterministic-only into shared space, never a synchronous prompt in the capture path.
2. **Stricter — no LLM anywhere:** rules or default-inbox only; ambiguity always drains through review. Zero classifier risk; the review queue does all multi-KB work.
3. **Looser — LLM may route to shared KBs above a very high bar:** better capture ergonomics for heavy work-KB users; accepts a nonzero chance of the trust-terminating event.

## How to decide

Evidence, not argument: replay two weeks of real captures (hand-labeled work/personal) through options 1 and 2 — measure misroute rate, review-queue depth, and how often option 2 merely defers what option 1 got right. The risk register (ARCHITECTURE Appendix B #2) sets the bar: >5% misroutes or a growing queue kills the classifier.

## Process

Runs alongside kb's build (build 1); decide before gtd-capture (build 3) sends real traffic through it. Auto-accept per RFC-003 window applies to the *choice among options*, not to skipping the replay.
