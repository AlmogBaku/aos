# Value vs blank agent — 2026-07-22

Runtime behavioral comparison: the RENDERED capture skill (from the committed golden
snapshot) + the live-scaffolded fixture KBs, vs a default assistant with nothing
installed. Four messages (whatsapp-channel personal item, explicit work: tag, untagged
idea, ticket keyword).

## Equipped agent (following the render mechanically)
- 4/4 routed correctly: channel rule -> personal, explicit tag -> shared (legal:
  explicitly tagged), default -> personal, keyword rule -> shared (legal: rule-matched).
- All entries parse against the format-entry grammar; Dana's timezone honored;
  confirmation = the MOD-injected single 🦜, no echo.
- Entries are durable (git-backed inbox), drainable (nightly triage), greppable.

## Blank agent
All four messages produce a friendly chat reply and nothing else: no persistence, no
routing, no reminder, information lost to future sessions. On the idea message it does
the exact anti-pattern (engages with content instead of capturing).

## Delta
persistence: durable KB lines vs chat scrollback · routing: deterministic precedence
with shared-KB safety vs none · retrievability: uniform grammar for drain/archiver vs
scrolling one conversation.

## Findings -> fixes (same day)
- entry-format now states the routing prefix is CONSUMED (stripped -> tag), and when
  #kb-routing-uncertain applies (step-4 fallback only).
- route skill now states keyword matching is case-insensitive substring, no semantics.
- Left open (harness-level, noted): batch-capture timestamps, confirmation batching.
