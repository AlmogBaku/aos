#!/usr/bin/env bash
# The one local gate: everything CI runs, runnable before every commit.
set -euo pipefail
cd "$(dirname "$0")/.."

# tier 0 — the kb tool: unit suite + the shipped example base must lint clean
# (template/example/tool drift breaks the build here, before anything else runs)
if command -v uv >/dev/null 2>&1; then
  uv run --quiet tests/tool/test_kb.py
  uv run --quiet tests/tool/test_cap.py
  uv run --quiet tests/tool/test_session.py
  # This lints a SHIPPED FIXTURE, so it runs in a fresh, empty aos home: with the default
  # one it would read the developer's real `~/aos/.aos/kb-registry.yaml` (its
  # confidence_bar) and identity, and the verdict would depend on whose machine ran it.
  # Lint is read-only and needs no identity, so none is pinned and any in the shell is
  # dropped — as is a registry the shell names.
  LINT_HOME="$(mktemp -d)"
  trap 'rm -rf "$LINT_HOME"' EXIT
  env -u AOS_REGISTRY -u AOS_PRINCIPAL_ID AOS_HOME="$LINT_HOME" \
  uv run --quiet --project capabilities/kb/tool kb \
    --base tests/fixtures/example-base lint | tee /tmp/example-base-lint.txt
  grep -q "Critical (0)" /tmp/example-base-lint.txt
  grep -q "Findings (0)" /tmp/example-base-lint.txt
else
  echo "check.sh: uv not found — tier-0 tool tests SKIPPED (install: https://docs.astral.sh/uv/)" >&2
fi

# tier 1 — kit lint + selftest, plus the repo-wide retired-token and coverage gates;
# tier 2 — golden structural checks.
# gates.template_drift is deliberately NOT here: it needs the network and reports offline
# as a skip, and a gate that fails on a plane is a gate people learn to skip. Run it by hand
# after touching templates/.
#
# uv is now the ONLY prerequisite — the whole toolchain is Python, so there is no npm ci and
# no node_modules. Tier 0 above degrades to a warning without uv, but tiers 1 and 2 cannot:
# they ARE the gate, and a run that silently skipped them would report success having checked
# nothing. So this fails loudly instead.
if ! command -v uv >/dev/null 2>&1; then
  echo "check.sh: uv is required for tiers 1-2 (install: https://docs.astral.sh/uv/)" >&2
  exit 1
fi
LINT="uv run --quiet --project tools/aos_lint python -m"
$LINT aos_lint.cli "$@"
$LINT aos_lint.selftest
$LINT aos_lint.gates.retired
$LINT aos_lint.gates.coverage
$LINT aos_lint.gates.kb_commands
$LINT aos_lint.gates.privacy
$LINT aos_lint.golden.check
