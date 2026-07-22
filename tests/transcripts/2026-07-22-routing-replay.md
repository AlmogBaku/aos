# Routing replay — 2026-07-22

Executor: Claude subagent, mechanically following capabilities/kb/skills/route/SKILL.md
against tests/fixtures/user-clone/kb-registry.yaml over tests/fixtures/routing-replay/cases.yaml.

## Result

- 20/20 cases PASS.
- Hard gate (a): zero `method: llm` outcomes into acme-kb (shared) — the private-only
  candidate filter excluded it by construction in every step-3 case.
- Hard gate (b): non-LLM cases 100% exact, including channel-beats-keyword precedence
  (case 11) and the unregistered-subject refusal path (case 20: payload preserved,
  refuse log + needs-review block).
- LLM cases: 2 resolved via llm, 0 misroutes (n too small to be RFC-006 evidence — the
  2-week live replay remains the real test).

## Findings → spec/artifact fixes

1. Tag→KB mapping was stored nowhere ("work:" named no KB) → registry entries now carry
   `tag:` (fixed same day; ledger row).
2. Within-step-2 channel-vs-keyword conflicts lean on prose ordering — tie-breaking is
   RFC-006's question; case 11 documents the current behavior.
3. Simulated classifier confidences on work-flavored untagged content (cases 16-18)
   hovered near the bar — at scale these drive the misroute statistic RFC-006 needs.
