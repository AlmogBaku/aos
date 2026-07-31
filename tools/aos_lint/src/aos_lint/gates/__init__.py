"""The standalone gates: repo-wide checks that are not part of the schema lint.

Each is its own entry point (`python -m aos_lint.gates.<name>`), as each was its own `node
tools/check-<name>.mjs` before the port — they answer different questions, fail for different
reasons, and `check.sh` runs them in sequence so a failure names one gate.
"""
