# Testing

How a capability proves it works (implements RFC-002).

## Tier 0 — capability tool tests (blocking)

`bash tools/check.sh` first runs the capability tool suites — kb's `kb`
(`uv run tests/tool/test_kb.py`) and capability-lifecycle's `aos-cap`
(`uv run tests/tool/test_cap.py`). Both invoke their tool's `cli:app` in-process via
typer's `CliRunner` (fast: kb's ~210 tests run in ~30s, aos-cap's ~110 in ~1s), asserting
on the same stdout/stderr/exit-code surface a real invocation produces — the report text
is still the contract, not tool internals. A `Result` adapter gives every assertion the
`.returncode`/`.stdout`/`.stderr` shape a subprocess result has, so the invocation layer
can change without touching test bodies. Each suite keeps exactly one real-subprocess
class (`InstalledScriptSmokeTest` / `InstalledScriptTest`): CliRunner never leaves the
process, so it can't prove `[project.scripts]` actually resolves as an installed console
script — that's the one thing those classes exist to check. `test_cap.py` additionally
needs a `chdir` helper, because a few of its behaviours (the cwd-upward `.aos/` search, a
relative `--artifact`, a relative capability dir) are genuine functions of the process
cwd, which an in-process runner inherits rather than isolates. What that suite must cover
— every verb, every failure mode, and the bug behind each regression pin — is indexed in
`tests/tool/COVERAGE-cap.md`, which is diffable against the file's `def test_*` names.
Tier 0 then lints the shipped example base (`tests/fixtures/example-base/`
must pass `kb lint` with zero criticals/findings — template/example/tool drift breaks the
build here). Requires `uv`; skipped locally with a warning if absent, always on in CI.

## Tier 1 — deterministic lint (blocking)

    bash tools/check.sh

The whole toolchain is Python, in the `tools/aos_lint` package — **`uv` is the only
prerequisite**, and every invocation below is prefixed with
`uv run --quiet --project tools/aos_lint python -m`.

Runs `aos_lint.cli` (89 checks in 15 code families over the §2/§3/§5 contracts — the
schema/contract linter, useful any time you're authoring a capability, not just for
testing), the lint selftest (`aos_lint.selftest` — every contract code must fire
on a planted-violation fixture, and a code that fires without being listed is also a
failure), and three gates the linter structurally cannot cover, because it validates schema
and these check *content*:

- **`aos_lint.gates.retired`** — repo-wide: no retired vocabulary survives, no artifact
  invokes the old command name, and every shipped skill description carries its trigger
  clause, a negative clause naming a **sibling** skill, and third person. Exemptions are
  deliberately narrow and each states its reason in the file: a short prefix allowlist for
  material that is *historical by nature* (transcripts, the append-only ledger, frozen
  snapshots, LAYOUT 1 fixtures), a per-file-and-per-token list for source that must NAME the
  old world in order to migrate it, and a `<!-- retired-ok: <tokens> -->` marker that exempts
  **only the tokens it names** — never the rest of the file.
- **`aos_lint.gates.coverage`** — every CLI verb is documented (parsed from the tool's own
  `--help`, so the list cannot drift), and every count quoted in prose is the count the
  tools report.
- **`aos_lint.gates.kb_commands`** — every documented `kb <verb> --flag`, in the
  capabilities *and* `docs/`, exists in the tool. Two careful human passes over the same
  prose still shipped nine commands that failed on invocation; that is the class this closes.

Then the golden structural checker. CI runs the same on every push/PR.

**Outside `check.sh` on purpose:** `aos_lint.gates.template_drift` compares the shipped
init templates against the `aos-kb-template` repo `kb init` clones. It needs the network and
reports offline as a *skip* — a gate that fails on a plane is a gate people learn to skip — so
run it by hand after touching `templates/`.

## Tier 2 — golden render (the e2e)

**No simulated harness.** The e2e is a real install into a disposable Hermes profile
namespace — see [`tests/golden/PROTOCOL.md`](../tests/golden/PROTOCOL.md). The checker and
normalizer are test-only code and live in `aos_lint.golden`; the data they operate on — the
protocol, the expectations, `prestate.sh`, and the snapshots — stays under `tests/golden/`:

    LINT="uv run --quiet --project tools/aos_lint python -m"
    bash tests/golden/prestate.sh tests/.sandbox/prestate-before.txt
    hermes profile create aos-test
    # tell the agent to install (PROTOCOL.md carries the exact prompt)
    $LINT aos_lint.golden.check --live full-install
    bash tests/golden/prestate.sh tests/.sandbox/prestate-after.txt
    diff tests/.sandbox/prestate-before.txt tests/.sandbox/prestate-after.txt  # canaries
    $LINT aos_lint.golden.normalize ~/.hermes/profiles/aos-test tests/golden/hermes/full-install/front
    # … then removal per the cheat-sheet, and prestate must match again

After the install e2e, the behavioral e2e ([`tests/golden/BEHAVIOR.md`](../tests/golden/BEHAVIOR.md) —
"a week in the life": capture burst w/ duplicate + injection sentinel, default-empty
promote, recall w/ citations + gap admission, state cap/staleness, authz probes,
sync-conflict with zero agent invocations, removal) runs against the same namespace;
each step has an observable expected outcome.

Committed snapshots under `tests/golden/hermes/` are re-checked deterministically in CI
(`aos_lint.golden.check`); the snapshot commit diff is the reviewable render.
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
