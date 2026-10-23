---
harness: badharness
status: maybe-later
rules: not-a-list
mapping:
  agent: {primitive: profile, support: via}
  main: {primitive: the default}
  skill: {primitive: a folder}
  cron: {support: none}
  context_block: {primitive: a file}
  secret: {primitive: an env line}
  config: {primitive: a key}
  hook: {support: via}
  session: {primitive: a session, open: "x <title>"}
  plan_mode: {support: maybe}
  messaging.inbound: {support: unknown}
  messaging.outbound: {support: unknown}
  voice.stt: {support: unknown}
  voice.tts: {support: unknown}
  calendar.read: {support: unknown}
  calendar.write: {support: unknown}
  teleportation: {support: unknown}
---
# bad-cap in-capability cheat-sheet

Planted violation: a cheat-sheet at the in-capability location
(`capabilities/<id>/harnesses/<runtime>.md`) with only one of the six required
§5.2 sections — `cheatsheet/section` must fire here too, proving the check
covers the capability-lifecycle path, not just top-level `harnesses/`.

## Primitive mapping

The only section present — the other five required §5.2 sections are missing.

Planted frontmatter violations for `cheatsheet/key`: no `source`/`files`, a bad `status`,
`rules` not a list, `email` missing (16 rows), an unknown row, a row with both `primitive`
and `support`, `support: maybe`, `via` without `via:`, `none` on a concept without
`instead:`, and a session row without `continue`/`id`/`missing`.
