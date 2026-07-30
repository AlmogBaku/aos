# kb

Knowledge infrastructure (ARCHITECTURE §4). A KB instance is a **base**: a git repo of
markdown, and nothing else. The capability ships:

- the user-owned registry (`kb-registry.yaml`) plus rules-first routing with a
  confidence-gated model fallback — shared bases **never** accept model-routed writes,
- the store itself: an immutable flat `_raw/`, current-truth wiki pages, and one
  tool-managed `.kb/` holding config, the attention window, and the single pending queue,
- the deterministic **`kb` tool** ([`tool/`](tool/), a `uv`-installed Python CLI; it never
  calls a model — RFC-004's outcome). `kb init` scaffolds by default from a cloned template
  repo (read-only, no fork); `--templates <local-dir>` skips the network, and a clone
  failure falls back to the templates shipped in this checkout,
- one **Archiver** agent across all bases (cross-base re-routing is its point), on two agent
  schedules plus a script-direct exec sync cron.

Skills, by the names they install under (`aos-lock skills` applies the prefix): `kb` (entry
— the runtime face), `kb-capture` (the sub-5s path when the user fires off a thought),
`kb-route` (destination resolution), `kb-recall` (cited answers with honest gaps), `kb-init`
(interview → scaffold → schedules), `kb-adopt` (register in place, report divergence, run
`kb migrate`), `kb-import` (interactive bulk import, source read-only always).

Two design notes worth reading before changing anything: **kb knows exactly one thing about
how long a page lives** (`expires:`, and `kb prune` acts on it — everything else is agent
judgment through `kb archive`), and **`.kb/pending/` is the only queue**, because a queue
file is justified only when the work item has no artifact of its own.

Deeper, for developers: [docs/design.md](docs/design.md) (why the base is shaped this way) ·
[docs/reference.md](docs/reference.md) (layout, frontmatter, verbs, query language, grants,
exit codes).

Contested core: the §4.2–4.3 routing and authorization behavior is
[RFC-006](https://github.com/AlmogBaku/aos/blob/spec/rfcs/RFC-006-multi-kb-routing.md) —
artifacts here build against the spec text, and the replay evidence decides the confidence
bar, tie precedence, and batching.

Spec one-pager: [kb.md](https://github.com/AlmogBaku/aos/blob/spec/capabilities/kb.md) ·
Deep dives: [the base engine](https://github.com/AlmogBaku/aos/blob/spec/design/kb-methodology.md) ·
[kb-authorization](https://github.com/AlmogBaku/aos/blob/spec/design/kb-authorization.md)

## Support matrix

| Harness | Status | Runner |
|---|---|---|
| Hermes | ✅ e2e-tested for real (install · promote · recall · removal) — **re-run owed at the current layout** | @AlmogBaku |
| NanoClaw (v1+v2), OpenClaw, Nanobot | 🧪 cheat-sheet shipped, research-drafted — no runner yet | — |
| Claude Code | 🧪 cheat-sheet shipped, research-drafted — no runner yet | — |
| OpenCode | 📋 no sheet yet — the no-cheat-sheet path applies | — |
