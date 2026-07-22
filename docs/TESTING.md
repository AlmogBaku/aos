# Testing

How a capability proves it works (implements RFC-002).

## Tier 1 — deterministic lint (blocking)

    bash tools/check.sh

Runs `tools/lint/aos-lint.mjs` (17 check families over the §2/§3/§5 contracts), the lint
selftest (`tools/lint/selftest/run.mjs` — every check must fire on a planted-violation
fixture), and the golden structural checker. CI runs the same on every push/PR.

## Tier 2 — golden render (the e2e)

**No simulated harness.** The e2e is a real install into a disposable Hermes profile
namespace — see [`tests/golden/PROTOCOL.md`](../tests/golden/PROTOCOL.md):

    bash tools/golden/prestate.sh tests/.sandbox/prestate-before.txt
    hermes profile create aos-test
    # tell the agent to install (PROTOCOL.md carries the exact prompt)
    node tools/golden/check.mjs --live full-install
    bash tools/golden/prestate.sh tests/.sandbox/prestate-after.txt
    diff tests/.sandbox/prestate-before.txt tests/.sandbox/prestate-after.txt  # canaries
    node tools/golden/normalize.mjs ~/.hermes/profiles/aos-test tests/golden/hermes/full-install/front
    # … then removal per the cheat-sheet, and prestate must match again

Committed snapshots under `tests/golden/hermes/` are re-checked deterministically in CI
(`node tools/golden/check.mjs`); the snapshot commit diff is the reviewable render.
Equivalence judging for re-renders: [`tests/golden/RUBRIC.md`](../tests/golden/RUBRIC.md).

## Scenario runs (tier-3-flavored, non-blocking)

- **Routing replay**: a subagent executes `capabilities/kb/skills/route/SKILL.md` over
  `tests/fixtures/routing-replay/cases.yaml`. Hard gates: all non-LLM cases exact; zero
  LLM routes into a shared KB. LLM-case misroutes are indicative RFC-006 evidence.
- **Interview round-trip**: fresh interview from
  `tests/fixtures/interview/onboarding.answers.yaml` → MOD.md; re-run must be a no-op;
  `--refresh` must show an empty diff for unchanged answers.
- Transcripts of real runs live in `tests/transcripts/`.

## Boundaries

`~/ai-kb` is never written. The live `~/.hermes` is touched only inside the
`aos-test`/`aos-*` profile namespace, with prestate snapshots proving the rest untouched.
The 2-week live routing replay is post-build (`docs/DOGFOOD.md` → RFC-006).
