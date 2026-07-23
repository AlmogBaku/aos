#!/usr/bin/env bash
# The one local gate: everything CI runs, runnable before every commit.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d node_modules ]; then
  npm ci --no-audit --no-fund
fi

# tier 0 — the base tool: unit suite + the shipped example base must lint clean
# (template/example/tool drift breaks the build here, before anything else runs)
if command -v uv >/dev/null 2>&1; then
  uv run --quiet tests/tool/test_base.py
  uv run --quiet --project capabilities/kb/tool base \
    --base tests/fixtures/example-base lint | tee /tmp/example-base-lint.txt
  grep -q "Critical (0)" /tmp/example-base-lint.txt
  grep -q "Findings (0)" /tmp/example-base-lint.txt
else
  echo "check.sh: uv not found — tier-0 tool tests SKIPPED (install: https://docs.astral.sh/uv/)" >&2
fi

# tier 1 — kit lint + selftest; tier 2 — golden structural checks
node tools/lint/aos-lint.mjs "$@"
node tools/lint/selftest/run.mjs
node tests/golden/check.mjs
