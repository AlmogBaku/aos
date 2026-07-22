---
name: adopt
description: Registers an existing knowledge base and reports how it diverges from its methodology — without rewriting anything. Use when the user already has a KB ("adopt ~/my-kb"), including during bootstrap.
x-aos-origin: kb@0.1.3
---

# adopt

`kb adopt <path>` — register, lint, report. **Zero writes into the KB.** Divergence is a
finding, never an error.

1. **[D]** Sanity: path exists; is a git repo (if not, offer `git init`, don't insist);
   not already registered.
2. **[D]** Interview the KB, not the user: does it have an `AGENTS.md`? `SCHEMA.md`?
   a `## Grants` (or maintainer/zone) table? an inbox? a `log.md`? Set `methodology:` to
   the closest match, or `none`.
3. **[D]** Register in `kb-registry.yaml` (shape in the init skill), asking only what the
   tree can't answer: `audience`, `purpose`, channel bindings, sync. Adopted KBs default
   `sync: manual` — auto-commit is opt-in only.
4. **[D]** Run the methodology lint in report-only mode: output to chat, nothing written
   into the KB. Structure: matches / divergences (schema violations, missing contract
   files, `.backup.*` files, format drift) / shortest convergence path if the user wants
   one (grants table → scheduled lint → fix schema drift as pages get touched).
5. Grants + archiver schedules only on explicit request — then exactly as the init skill
   does, through the diff gate.
