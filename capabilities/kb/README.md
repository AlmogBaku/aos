# kb

Multi-base knowledge infrastructure (ARCHITECTURE §4). A KB instance is a **base**
(`base == repo`). The capability ships:

- the user-owned registry (`kb-registry.yaml`) + rules-first routing with a
  confidence-gated LLM fallback (shared bases **never** accept LLM-routed writes),
- the **base engine** — store (immutable `raw/` + current-truth wiki pages under a
  per-base `BASE.yaml`), curation (`base capture` → skeptical default-empty promotion
  → lint → review queue), state (one capped `state.yaml` attention window per base),
- the deterministic **`base` tool** (bundled in the entry skill:
  capture/inbox/state/search/links/lint/grants/index/sync/verify — never calls an
  LLM; RFC-004's outcome),
- one **Archiver** agent across all bases (cross-base re-routing is its point), on
  two agent schedules plus a script-direct **exec** sync cron.

Skills: `kb` (entry — the runtime face), `route` (write path), `recall` (read path
with citations + gap admission), `init` (interview → BASE.yaml → scaffold), `adopt`
(register + divergence report, zero writes). The kb capability *is* the methodology
(Karpathy-LLM-wiki lineage, extended — see the spec's lineage table); no pluggable
seam in v0.1.

Contested core: the §4.2–4.3 routing/authorization behavior is
[RFC-006](https://github.com/AlmogBaku/aos/blob/spec/rfcs/RFC-006-multi-kb-routing.md)
— artifacts here build against the spec text; the replay evidence decides the
confidence bar, tie precedence, and drain batching.

Spec one-pager: [kb.md](https://github.com/AlmogBaku/aos/blob/spec/capabilities/kb.md) · Deep dives:
[the base engine](https://github.com/AlmogBaku/aos/blob/spec/design/kb-methodology.md) ·
[kb-authorization](https://github.com/AlmogBaku/aos/blob/spec/design/kb-authorization.md)

## Support matrix

| Harness | Status | Runner |
|---|---|---|
| Hermes | hook | @AlmogBaku |
| NanoClaw | unsupported (no runner yet) | — |
| OpenClaw | unsupported (no runner yet) | — |
