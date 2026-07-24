---
x-aos-origin: capability-lifecycle@0.1.0
name: capability-upgrader
description: Upgrades installed aos capabilities by re-applying the user's MOD.md ledger to fresh upstream. Use when the user says "update" or "upgrade" (the whole kit or one capability), or after a git pull of the aos clone.
---

# capability-upgrader

Not in context yet? Load the `capability-lifecycle` skill first. The model: **MOD.md is
a ledger; upgrade = re-apply it to fresh upstream.** The current install is a drift
source, never a merge input.

1. **[D]** Scope: the named capability, else every entry in `aos-lock list`.
2. **[D]** Kit-wide: `git -C <clone> pull` — upstream overrides shipped files; the
   overlay family is untouched by construction. A capability needs work when its
   manifest version (`aos-lock manifest`) ≠ its lockfile version.
3. Per capability needing work:
   a. **[D]** `aos-lock verify <id>` — drift (the user's hand-edits) → **[A]** fold each
      into MOD.md first per `reference/overlay.md` ("you changed X — keeping it").
   b. **[D]** Back up the materialized artifacts (`aos-lock show <id>` lists them) →
      `<clone>/.aos/backups/`.
   c. **[A]** Re-render: fresh upstream × MOD.md — the same transform as install
      (`reference/overlay.md`); interview only new or `re_ask` questions. Then STAGE
      the changes per the cheat-sheet (load it now if not in context).
   d. **[D]** GATE: old render vs new, per file.
   e. **[D]** EXECUTE; `aos-lock record <id>` re-hashes.
4. Report per capability: upstream changes taken, ledger entries re-applied, anything
   folded in step a.
