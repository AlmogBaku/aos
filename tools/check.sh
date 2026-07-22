#!/usr/bin/env bash
# The one local gate: everything CI runs, runnable before every commit.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d tools/node_modules ]; then
  npm ci --prefix tools --no-audit --no-fund
fi

node tools/lint/aos-lint.mjs "$@"
node tools/lint/selftest/run.mjs

if [ -f tools/golden/check.mjs ]; then
  node tools/golden/check.mjs
fi
