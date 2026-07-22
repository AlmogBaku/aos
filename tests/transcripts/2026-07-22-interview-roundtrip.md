# Interview round-trip — 2026-07-22

Executor: Claude subagent playing interviewer (per capabilities/onboarding/skills/
interview/SKILL.md) and scripted fixture user (tests/fixtures/interview/
onboarding.answers.yaml), three runs.

## Result — all PASS

1. Fresh run: answers frontmatter keys == the six question ids exactly; values pass
   answer-validation; all asides landed as body prose under the right headings; nothing
   leaked into frontmatter. Frontmatter byte-identical to the user-clone reference MOD.
2. Re-run: exactly one question re-asked (sacred_time, the only re_ask: true);
   result byte-identical to run 1 — the no-op property holds.
3. --refresh: all questions re-asked with defaults; identical answers ⇒ empty diff.

## Findings → fixes (same day)

- Fixture drift: the reference MOD carried red-lines prose the answers fixture never
  scripted → answers.yaml now scripts those asides.
- Skill under-specified: empty-diff behavior (now: no write, no prompt),
  never-re-serialize rule (byte-stability is what makes no-op testable),
  onboarded_version source (CAPABILITY.md version), no empty headings.
- Noted, not changed (rule of two): enum options live in script prose, so the tier-1
  linter can't machine-check enum answer values.
