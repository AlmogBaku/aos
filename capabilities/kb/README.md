# kb

Multi-KB infrastructure (ARCHITECTURE §4): the user-owned registry (`kb-registry.yaml`),
rules-first routing with a confidence-gated LLM fallback (shared KBs **never** accept
LLM-routed writes), per-KB authorization via a `## Grants` table, and one shipped
methodology — [`karpathy-3layer`](methodologies/karpathy-3layer/) — with its Archiver
agent and schedules.

Skills: `route` (resolve a write intent to a KB), `authz-check` (grant-table lookup —
shared with the permission gate), `init` (scaffold + register + **schedule the maintainer
in the same session**), `adopt` (register an existing KB, report divergence, rewrite
nothing).

Contested core: the §4.2–4.3 routing/authorization behavior is
[RFC-006](https://github.com/AlmogBaku/aos/blob/spec/rfcs/RFC-006-multi-kb-routing.md) — artifacts here build against the spec
text; the replay evidence decides the confidence bar, tie precedence, and drain batching.

Spec one-pager: [kb.md](https://github.com/AlmogBaku/aos/blob/spec/capabilities/kb.md) · Deep dives:
[kb-methodology](https://github.com/AlmogBaku/aos/blob/spec/design/kb-methodology.md) ·
[kb-authorization](https://github.com/AlmogBaku/aos/blob/spec/design/kb-authorization.md)

## Support matrix

| Harness | Status | Runner |
|---|---|---|
| Hermes | hook | @AlmogBaku |
| NanoClaw | unsupported (no runner yet) | — |
| OpenClaw | unsupported (no runner yet) | — |
