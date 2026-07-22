# Importer acceptance — trip-planning, 2026-07-22

Real run of capabilities/importer/skills/import against the live Hermes (read-only,
verified: zero writes to ~/.hermes or ~/ai-kb; ai-kb working tree clean). Draft emitted
to the sandbox only — the draft MOD.md holds real nuances and is never committed.

## Result — acceptance bar met
- Inventory: 2 hand-rolled skills (+scripts/references), 0 travel crons (4 keyword hits
  verified incidental and excluded), 1 uninitialized state DB, 1 secret (name only),
  1 KB zone convention incl. a router contract living in a KB build-plan file.
- Cluster: skills + state + secret ref + trips zone + live-trip operating contract;
  adjacent-excluded list offered (gateway whitelisting -> permission-gate territory,
  kb sync -> kb capability).
- Map: skills -> skills/ (flattened), KB conventions -> kb/zones/ + kb.writes/zones,
  contract-in-KB-file -> a new trip-mode skill (judgment, GAP'd), secret -> {store,key}
  ref + GAP entry, drifted JSON DB -> not imported (GAP drift).
- Split examples: quality thresholds -> {{mod}} slot + onboarding question; delivery
  format -> MOD; hardcoded channel id -> reference-only slot with an explicit
  "references, not raw ids" onboarding instruction.
- Emitted: 18 files; manifest verified against the §2.2 field set; every skill a valid
  Agent Skills folder with used_by; GAP.md: 14 entries (1 secret, 2 hardcoded-path,
  3 drift, 2 harness-only, 4 judgment, 1 not-imported, 1 secret-adjacent).
- PR distance: polishable in under an hour (punch list = 4 judgment confirmations,
  one dedup, one DB decision, the -draft rename). Expected lint warn: all-main
  scoping — genuine for this capability, pre-answered in its README.

## Spec feedback
No contract failures. The 2 harness-only GAP entries are standing evidence for future
§5.2 vocabulary discussion (messaging channel binding); nothing to change now.
