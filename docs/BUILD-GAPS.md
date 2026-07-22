# Build-gap ledger

Append-only. Every mismatch the build phase finds between an artifact and the spec gets a row.
The spec fix lands **in the same commit** as the artifact that revealed the gap (firm-position
discipline, ARCHITECTURE §8). Anything in an open RFC's territory is appended to that RFC as
evidence — never quietly fixed in ARCHITECTURE. A proposed new frontmatter field must name its
two in-repo machine consumers (rule of two) or stay prose.

| Date | WP | Spec section | Mismatch | Resolution |
|---|---|---|---|---|
| 2026-07-22 | WP3 (pre-seeded) | design/kb-methodology.md §8 vs ARCHITECTURE §2.1 | `archiver.agent.yaml` placed inside the methodology dir by kb-methodology §8, but §2.1 and kb-authorization put agent specs in `agents/` (where `schedules[].agent` resolves) | open — expected resolution: canonical in `agents/`, prompts stay in methodology dir, fix kb-methodology §8 |
| 2026-07-22 | WP3 (pre-seeded) | ARCHITECTURE §2.1 / §3.1 | ONBOARDING.md question `type` vocabulary is never enumerated anywhere | open — expected resolution: define minimal set (`string\|number\|boolean\|enum\|list\|path`, orthogonal `secret`), lint enforces |
| 2026-07-22 | WP6 (pre-seeded) | ARCHITECTURE §2.1 | Is `MOD.example.md` required when a capability has no ONBOARDING.md (importer)? | open — expected resolution: optional, presence-paired with ONBOARDING.md |
