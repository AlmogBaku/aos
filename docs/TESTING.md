# Testing

How a capability proves it works (implements RFC-002; filled in as the tiers land).

## Tier 1 — deterministic lint (blocking)

    bash tools/check.sh

Runs `node tools/lint/aos-lint.mjs` over the whole tree. Landing in WP1.

## Tier 2 — golden render (blocking once adapters exist)

E2E verification is a **real install**: create a disposable Hermes profile (`aos-test`) and
tell its agent to install the capability, given only the capability dir +
`harnesses/hermes/CHEATSHEET.md` + a fixture `MOD.md`. Deterministic structural checks run
over the materialized artifacts; the normalized render is committed under `tests/golden/`.
Protocol lands in WP5 (`tests/golden/PROTOCOL.md`).

## Tier 3 — scenario transcripts (non-blocking)

Run transcripts saved under `tests/transcripts/` as evidence.
