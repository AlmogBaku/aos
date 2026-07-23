#!/usr/bin/env bash
# The one local gate: everything CI runs, runnable before every commit.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d node_modules ]; then
  npm ci --no-audit --no-fund
fi

node tools/lint/aos-lint.mjs "$@"
node tools/lint/selftest/run.mjs
node tests/golden/check.mjs
