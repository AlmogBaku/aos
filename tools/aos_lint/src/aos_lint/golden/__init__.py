"""The golden-render machinery (RFC-002 tier 2, deterministic layer).

Test-only, which is why the .mjs originals lived in tests/golden/ rather than tools/. They
live in this package now because it is the one installable Python project on the repo side —
`normalize` and `check` share the SKIP set and the origin-stamp reader, and importing across
tests/ would mean a second package for two modules. The entry points keep their old names
(`python -m aos_lint.golden.check`, `... .normalize`), and tests/golden/ keeps everything
that is data: PROTOCOL.md, the expectations, the snapshots, prestate.sh.
"""
