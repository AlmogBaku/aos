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
   change, or a self-drafted cheat-sheet branch): skip the pull, say so, name the
   branch, and say how to resume upstream updates
   (`git -C <home>/upstream switch main`). A capability
   needs work when its manifest version (`aos-lock manifest`) ≠ its lockfile version.
   Migration note: overlay files found *inside* the clone (a pre-household install) →
   offer the one-time move into `personal/` before anything else.
3. Per capability needing work:
   a. **[D]** `aos-lock verify <id>` — two classes, two responses. *Artifact drift*
      (a render file's hash changed = the user's hand-edit) → **[A]** fold each into
      MOD.md first per `reference/overlay.md` ("you changed X — keeping it").
      *Link damage* (`MISSING LINK`, `NOT A LINK (copies are banned)`, `RELINKED`,
      `DANGLING LINK`) is not a hand-edit and never folds: re-create the link from the
      lockfile's recorded target, say what you repaired, and stop if the target itself
      is gone (that is a broken install, not an upgrade). A
      fold that reaches beyond the `{{mod}}` slots is mechanism-shaped — note it for
      the promotion judgment (overlay.md, Promote and retire), end of conversation.
   b. **[A]** Re-render: fresh upstream × MOD.md — the same transform as install
      (`reference/overlay.md`), written into `personal/`'s working tree; interview
      only new or `re_ask` questions. Then STAGE any native-plan changes per the
      cheat-sheet (load it now if not in context).
   c. **[D]** GATE: stage this capability, then diff it — `git -C <home>/personal add
      -A -- capabilities/<id>` then `git -C <home>/personal diff --staged --
      capabilities/<id>` — the old render vs the new, per file, **including files the
      re-render added** (a bare `git diff` hides them) — plus the native plan. Approve
      → commit (dated message). Decline → `git -C <home>/personal restore --staged
      --worktree -- capabilities/<id>`, then `git -C <home>/personal clean -fd --
      capabilities/<id>` as belt-and-braces (restore already removes the staged
      additions; clean catches anything staging missed), stop. Keep every command
      path-scoped: unscoped staging or resetting would capture — or destroy —
      unrelated work elsewhere in `personal/`. Before staging, `git status --
      capabilities/<id>`: a pre-existing untracked file of the user's in that directory
      would be swept in and lost on decline — name it to them first.
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
