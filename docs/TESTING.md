# Testing

How a capability proves it works (implements RFC-002).

## Tier 0 — capability tool tests (blocking)

`bash tools/check.sh` first runs the capability tool suites — kb's `kb`
(`uv run tests/tool/test_kb.py`) and capability-lifecycle's `aos-lock`
(`uv run tests/tool/test_lock.py`). `test_kb.py` invokes `aos_kb.cli:app` in-process via
typer's `CliRunner` (fast: the whole suite runs in ~20s), asserting on the same
stdout/stderr/exit-code surface a real invocation produces — the report text is still the
contract, not tool internals. A `Result` adapter gives every assertion the
`.returncode`/`.stdout`/`.stderr` shape a subprocess result has, so the invocation layer
can change without touching test bodies. One class, `InstalledScriptSmokeTest`, stays a
real subprocess: CliRunner never leaves the process, so it can't prove `[project.scripts]
kb = ...` actually resolves as an installed console script — that's the one thing this
class exists to check. It then lints the shipped example base (`tests/fixtures/example-base/`
must pass `kb lint` with zero criticals/findings — template/example/tool drift breaks the
build here). Requires `uv`; skipped locally with a warning if absent, always on in CI.

## Tier 1 — deterministic lint (blocking)

    bash tools/check.sh

Runs `tools/lint/aos-lint.mjs` (81 checks in 13 code families over the §2/§3/§5 contracts — the
schema/contract linter, useful any time you're authoring a capability, not just for
testing), the lint selftest (`tools/lint/selftest/run.mjs` — every contract code must fire
on a planted-violation fixture, and a code that fires without being listed is also a
failure), and the golden structural checker. CI runs the same on every push/PR.

## Tier 2 — golden render (the e2e)

**No simulated harness.** The e2e is a real install into a disposable Hermes profile
namespace — see [`tests/golden/PROTOCOL.md`](../tests/golden/PROTOCOL.md). The checker,
normalizer, and prestate script are test-only and live under `tests/golden/` alongside
the fixtures and snapshots they operate on:

    bash tests/golden/prestate.sh tests/.sandbox/prestate-before.txt
    hermes profile create aos-test
    # tell the agent to install (PROTOCOL.md carries the exact prompt)
    node tests/golden/check.mjs --live full-install
    bash tests/golden/prestate.sh tests/.sandbox/prestate-after.txt
    diff tests/.sandbox/prestate-before.txt tests/.sandbox/prestate-after.txt  # canaries
    node tests/golden/normalize.mjs ~/.hermes/profiles/aos-test tests/golden/hermes/full-install/front
    # … then removal per the cheat-sheet, and prestate must match again

After the install e2e, the behavioral e2e ([`tests/golden/BEHAVIOR.md`](../tests/golden/BEHAVIOR.md) —
"a week in the life": capture burst w/ duplicate + injection sentinel, default-empty
promote, recall w/ citations + gap admission, state cap/staleness, authz probes,
sync-conflict with zero agent invocations, removal) runs against the same namespace;
each step has an observable expected outcome.

Committed snapshots under `tests/golden/hermes/` are re-checked deterministically in CI
(`node tests/golden/check.mjs`); the snapshot commit diff is the reviewable render.
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
