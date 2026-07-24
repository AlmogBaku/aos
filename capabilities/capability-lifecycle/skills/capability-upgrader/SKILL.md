---
name: capability-upgrader
description: Upgrades installed aos capabilities by re-applying the user's MOD.md ledger to fresh upstream. Use when the user says "update" or "upgrade" (the whole kit or one capability), or after a git pull of the aos upstream clone.
---

# capability-upgrader

Not in context yet? Load the `capability-lifecycle` skill first — the map, the
contract, the overlay doctrine, and the Experience rules. The model: **MOD.md is
a ledger; upgrade = re-apply it to fresh upstream, into `personal/`'s working tree.**
The current install is a drift source, never a merge input; the review gate is a git
diff in the user's own repo.

1. **[D]** Scope: the named capability, else every entry in `aos-lock list`.
2. **[D]** Kit-wide: pull `<home>/upstream` from the canonical remote (`git pull
   upstream main` when an `upstream` remote exists, else `git pull`) — it cannot touch
   `personal/`, a different repo. On a non-`main` branch (a contributor dogfooding a
   change): skip the pull, say so, and name the branch in the report. A capability
   needs work when its manifest version (`aos-lock manifest`) ≠ its lockfile version.
   Migration note: overlay files found *inside* the clone (a pre-household install) →
   offer the one-time move into `personal/` before anything else.
3. Per capability needing work:
   a. **[D]** `aos-lock verify <id>` — drift (the user's hand-edits) → **[A]** fold each
      into MOD.md first per `reference/overlay.md` ("you changed X — keeping it"). A
      fold that reaches beyond the `{{mod}}` slots is mechanism-shaped — note it for
      the promotion judgment (overlay.md, Promote and retire), end of conversation.
   b. **[A]** Re-render: fresh upstream × MOD.md — the same transform as install
      (`reference/overlay.md`), written into `personal/`'s working tree; interview
      only new or `re_ask` questions. Then STAGE any native-plan changes per the
      cheat-sheet (load it now if not in context).
   c. **[D]** GATE: `git -C <home>/personal diff` — the old render vs the new, per
      file — plus the native plan. Approve → commit (dated message); decline →
      `git -C <home>/personal checkout -- .` restores the working tree, stop.
   d. **[D]** EXECUTE the native plan (links usually survive re-render untouched —
      verify, don't assume); `aos-lock record <id>` with the full updated set (start
      from `aos-lock show` — `record` replaces the entry wholesale, never call it with
      a partial list; keep `--source-root` and `--link` records).
   e. **[A]** Retirement pass (overlay.md, Promote and retire): fresh upstream now
      covers a ledger line — a new interview question over its subject, or the
      behavior baked in → offer to retire the line (diff-shown; written only through
      `capability-evolver`).
4. Report per capability: upstream changes taken, ledger entries re-applied, lines
   retired, anything folded in step a — and at most one promotion offer, if a fold
   qualified.
