---
name: adopt
description: Registers an existing knowledge base and reports how it diverges from its methodology — without rewriting anything. Use when the user already has a KB ("adopt ~/my-kb"), including during bootstrap.
x-aos-origin: kb@0.1.0
---

# adopt

`kb adopt <path>` — register, lint, report. **Never rewrite the user's KB.** Their tree,
their conventions, their mess: adoption means the kit starts *reading* it and honestly
reports the distance to the methodology, so the user can close the gap on their own terms
(or not).

## Steps

1. **[D] Sanity**: the path exists, is a git repo (if not: offer `git init`, don't insist),
   and is not already registered.
2. **[D] Interview the KB** (not the user): does an `AGENTS.md` contract exist? A
   `SCHEMA.md`? A `## Grants` (or maintainer/zone) table? An inbox? A `log.md`? Which
   methodology does it most resemble? Set `methodology:` accordingly — or `none`; adoption
   does not require the shipped methodology.
3. **[D] Register** it in `kb-registry.yaml` (same shape as in the init skill), asking only
   for what can't be read from the tree: `audience`, `purpose`, channel bindings, sync
   preference. Default `sync: manual` for adopted KBs — never start auto-committing to a
   repo the kit didn't create without the user opting in.
4. **[D] Lint, report-only**: run the methodology lint checks against the tree and write
   the divergence report to **stdout/chat, not into the KB** (the KB gets no writes at
   all during adoption). Structure: what matches, what diverges (schema violations, missing
   contract files, stale content, `.backup.*` files, format drift), and — if the user wants
   to converge — the shortest ordered path (usually: add a Grants table → add lint to a
   schedule → fix schema drift as pages get touched, never as a big bang).
5. **Grants + schedules only on request.** If (and only if) the user wants the archiver to
   maintain this KB: draft the grant rows and create the schedules exactly as the init
   skill does, through the normal diff gate.

## Acceptance posture

This skill's bar (capability one-pager): adopting a real production KB runs clean —
meaning the *adoption* completes with a useful report even when the KB itself is far from
the methodology. Divergence is a finding, never an error.
