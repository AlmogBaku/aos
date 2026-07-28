# kb

Multi-base knowledge infrastructure (ARCHITECTURE §4). A KB instance is a **base**
(`base == repo`). The capability ships:

- the user-owned registry (`kb-registry.yaml`) + rules-first routing with a
  confidence-gated LLM fallback (shared bases **never** accept LLM-routed writes),
- the **base engine** — store (immutable `_raw/` + current-truth wiki pages under a
  per-base `.kb/base.yml`), curation (`kb capture` → skeptical default-empty promotion
  → lint → the one `.kb/pending/` queue), state (one capped attention window per base,
  sharded per principal under `.kb/state/`),
- the deterministic **`kb` tool** ([`tool/`](tool/), a `uv`-installed, `typer`-driven
  Python CLI on PATH as `kb` — verbs: init, adopt, migrate, capture, ingest, pending,
  inbox, find, state, search, links, lint, grants, index, sync, set, prune, archive,
  verify, config, commit, history, refuse, import survey; never calls an LLM; RFC-004's
  outcome). `kb init` scaffolds by default from a cloned template repo (read-only, no
  fork; `--templates <local-dir>` skips the network step; a clone failure falls back to
  the templates shipped in this checkout),
- one **Archiver** agent across all bases (cross-base re-routing is its point), on
  two agent schedules plus a script-direct **exec** sync cron.

Skills, by the names they install under (the source ids drop the `kb-` prefix, which
`aos-lock skills` applies): `kb` (entry — the runtime face), `kb-route` (write path),
`kb-recall` (read path with citations + gap admission), `kb-init` (interview → scaffold
via a cloned template), `kb-adopt` (register + divergence report, zero writes), `kb-import`
(interactive bulk import of an existing KB — source read-only always; the ~/ai-kb
migration path). The kb capability *is* the methodology
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
| Hermes | ✅ e2e-tested for real (install · promote · recall · removal) | @AlmogBaku |
| NanoClaw (v1+v2), OpenClaw, Nanobot | 🧪 cheat-sheet shipped, research-drafted — no runner yet | — |
| Claude Code, OpenCode | 📋 no sheet yet — the no-cheat-sheet path applies | — |
