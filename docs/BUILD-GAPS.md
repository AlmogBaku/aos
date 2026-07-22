# Build-gap ledger

Append-only. Every mismatch the build phase finds between an artifact and the spec gets a row.
The spec fix lands **in the same commit** as the artifact that revealed the gap (firm-position
discipline, ARCHITECTURE §8). Anything in an open RFC's territory is appended to that RFC as
evidence — never quietly fixed in ARCHITECTURE. A proposed new frontmatter field must name its
two in-repo machine consumers (rule of two) or stay prose.

| Date | WP | Spec section | Mismatch | Resolution |
|---|---|---|---|---|
| 2026-07-22 | WP3 (pre-seeded) | design/kb-methodology.md §8 vs ARCHITECTURE §2.1 | `archiver.agent.yaml` placed inside the methodology dir by kb-methodology §8, but §2.1 and kb-authorization put agent specs in `agents/` (where `schedules[].agent` resolves) | **fixed in kb-methodology §8**: canonical in `agents/`, prompts in `methodologies/*/archiver/` |
| 2026-07-22 | WP3 (pre-seeded) | ARCHITECTURE §2.1 / §3.1 | ONBOARDING.md question `type` vocabulary is never enumerated anywhere | **resolved in artifacts**: `string\|number\|boolean\|enum\|list\|path` + orthogonal `secret` (lint enforces; normative text = onboarding interview skill) |
| 2026-07-22 | WP3 | ARCHITECTURE §2.2 | Methodology-shipped skills (karpathy-3layer `lint/`) can't appear in manifest `skills[]` (path fixed to `skills/<id>/`), so they have no `used_by` declaration | **documented in kb-methodology §8**: the methodology contract carries them; they materialize with the archiver. Rule-of-two: no new manifest field |
| 2026-07-22 | WP6 (pre-seeded) | ARCHITECTURE §2.1 | Is `MOD.example.md` required when a capability has no ONBOARDING.md (importer)? | open — expected resolution: optional, presence-paired with ONBOARDING.md |
| 2026-07-22 | WP2 | ARCHITECTURE §5.3 | Hermes agent row claimed "profile + entry in config.yaml" — profiles are directory-defined; no config.yaml registry exists | **fixed in §5.3** (same commit as the Hermes cheatsheet); create via `hermes profile create` |
| 2026-07-22 | WP2 | ARCHITECTURE §5.3 | Hermes schedule row said write `jobs.json` "tagged `origin: aos:<cap>@<ver>`" — jobs.json is scheduler-owned (live state, schema drift) and its `origin` field already means chat provenance | **fixed in §5.3**: `hermes cron create` + `aos:<cap>:<id>` name prefix + lockfile job id |
| 2026-07-22 | WP2 | ARCHITECTURE §3.1, §5.3 | Secret store named `auth.json`/`hermes-auth` — auth.json is Hermes's provider-credential state; capability secret values live in `.env` | **fixed** (§3.1 example → `{store: hermes-env, key: VAR}`; §5.3 secret row) |
