---
id: session
version: 0.1.1
tags: [infra]
summary: Opens a new titled session for the person, or adds a turn to the session that asked for the work — through the harness's own command line, driven by the household's cheat-sheet.
depends:
  capabilities: [capability-lifecycle]
skills:
  - id: session
    used_by: [main]
---

# session — installer's briefing

A capability that must reach the person outside a running conversation — a cron job that
opens this week's interview, a hook that tells the operator a guest finished — calls
`aos-session`. It holds no harness knowledge of its own: the household's `.aos/harness.yml`
(written by `aos-cap harness set`, capability-lifecycle) names the installed cheat-sheet, and
that sheet's `mapping.session` row supplies the command templates and the patterns that read the
harness's answer. A new harness is a new sheet, never new code.

0. **The tool — first.** `uv tool install --from <aos_home>/upstream/capabilities/session/tool
   aos-session` → `aos-session` on PATH. Record the resolved binary (`readlink -f $(command -v
   aos-session)`) as an `--artifact`; removal is `uv tool uninstall aos-session`.
1. **The harness record.** `aos-cap harness show` must print the household's harness with a
   `cli` path. When the sheet's `mapping.session` has no `primitive`, every call exits 4: say in
   the install summary that sessions are unavailable on this harness and that each caller takes
   its own declared fallback.
2. **The skill.** Link the entry skill per `used_by`. A capability whose own agent opens
   sessions (a cron agent) declares a `uses` row for this skill.

The tool never notifies by other means and has no fallback: a failure exits non-zero with the
reason, and the caller decides what follows (exit codes in `skills/session/SKILL.md`).
