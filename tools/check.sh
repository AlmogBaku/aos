#!/usr/bin/env bash
# The one local gate: everything CI runs, runnable before every commit.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d node_modules ]; then
  npm ci --no-audit --no-fund
fi

# tier 0 — the kb tool: unit suite + the shipped example base must lint clean
# (template/example/tool drift breaks the build here, before anything else runs)
if command -v uv >/dev/null 2>&1; then
  uv run --quiet tests/tool/test_kb.py
  uv run --quiet tests/tool/test_lock.py
  # AOS_PRINCIPAL_ID is pinned because this lints a SHIPPED FIXTURE, and "who is calling"
  # is not a property of that fixture. Without it the tool synthesizes an identity from the
  # host — and on a CI runner that is `runner@runnervm….local`, whose `.local` suffix is
  # exactly what `is_weak_principal` is built to catch. So the check failed on the runner's
  # hostname while passing on every developer machine that has a git identity: a red build
  # saying nothing about the fixture. The weak-principal check itself is right and stays.
  AOS_PRINCIPAL_ID=dana@example.com \
  uv run --quiet --project capabilities/kb/tool kb \
    --base tests/fixtures/example-base lint | tee /tmp/example-base-lint.txt
  grep -q "Critical (0)" /tmp/example-base-lint.txt
  grep -q "Findings (0)" /tmp/example-base-lint.txt
else
  echo "check.sh: uv not found — tier-0 tool tests SKIPPED (install: https://docs.astral.sh/uv/)" >&2
fi

# tier 1 — kit lint + selftest, plus the repo-wide retired-token and coverage gates;
# tier 2 — golden structural checks.
# check-template-drift.mjs is deliberately NOT here: it needs the network and reports offline
# as a skip, and a gate that fails on a plane is a gate people learn to skip. Run it by hand
# after touching templates/.
node tools/lint/aos-lint.mjs "$@"
node tools/lint/selftest/run.mjs
node tools/check-retired.mjs
node tools/check-coverage.mjs
node tools/check-kb-commands.mjs
node tests/golden/check.mjs
