---
name: capability-upgrade
description: Upgrades installed aos capabilities by re-applying the user's MOD.md deltas to fresh upstream. Use when the user says "update" or "upgrade" (the whole kit or one capability), or after a git pull of the aos upstream clone.
x-aos-origin: capability-lifecycle@0.3.0
---

# capability-upgrade

Not in context yet? Load the `capability-lifecycle` skill first — the map, the
contract, the overlay doctrine, and the Experience rules. The model: **MOD.md states
the user's deltas; upgrade = re-apply them to fresh upstream, into `personal/`'s
working tree.**
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
   offer the one-time move into `personal/` before anything else. Referenced third-party
   skills come along: for each recorded link into `<home>/vendor`, `git -C <vendor-clone>
   pull --ff-only` (or the harness's plugin update), then re-`record` so the hashes match.
   Offline or a dirty clone → say so and continue; a stale reference is never a blocker.
3. Per capability needing work:
   a. **[D]** `aos-lock verify <id>` — two classes, two responses. *Artifact drift*
      (a render file's hash changed = the user's hand-edit) → **[A]** fold each into
      MOD.md first per the `capability-lifecycle` skill's `reference/overlay.md` (edit the
      statement that covers it — never
      append a contradicting one) ("you changed X — keeping it").
      *Link damage* (`MISSING LINK`, `NOT A LINK (copies are banned)`, `RELINKED`,
      `DANGLING LINK`) is not a hand-edit and never folds: re-create the link from the
      lockfile's recorded target, say what you repaired, and stop if the target itself
      is gone (that is a broken install, not an upgrade). A
      fold that reaches beyond the `{{mod}}` slots is mechanism-shaped — note it for
      the promotion judgment (overlay.md, Promote and retire), end of conversation.
   b. **[D]** Name gate: `aos-lock --home <home> skills <dir> --check --harness-skills
      <each skills dir this harness reads>`. Upstream may have renamed or added a skill, so the installed
      names can differ from the recorded links — a rename means link the new name and drop
      the old one in step d. Exit 17 → stop and report; never rename locally. This
      capability's own links are exempt, so a plain re-render is always clean.
   c. **[A]** Re-render: `aos-lock render <dir> <skill-id> --out
      <home>/personal/capabilities/<id>/skills --force` per declared skill, then fresh
      upstream × MOD.md — the same transform as install (`reference/overlay.md`), written
      into `personal/`'s working tree; interview only new or `re_ask` questions. A skill
      whose installed name changed leaves its old render directory behind: delete it in the
      same commit, so the diff shows the rename as one move. Then STAGE any native-plan
      changes per the cheat-sheet (load it now if not in context).
   d. **[D]** GATE: stage this capability, then diff it — `git -C <home>/personal add
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
   e. **[D]** EXECUTE the native plan (links usually survive re-render untouched —
      verify, don't assume); `aos-lock record <id>` with the full updated set (start
      from `aos-lock show` — `record` replaces the entry wholesale, never call it with
      a partial list; keep `--source-root` and `--link` records).
   f. **[A]** Retirement pass (overlay.md, Promote and retire): fresh upstream now
      covers a MOD statement — a new interview question over its subject, or the
      behavior baked in → offer to retire it (diff-shown; written only through
      `capability-evolve`).
4. **Absorbed capabilities.** A lockfile entry whose capability no longer exists upstream
   was folded into another one (0.3.0 absorbed `onboarding`, `importer`, and
   `capability-builder` into `capability-lifecycle`). Say what happened, then: unlink that
   entry's skill links, `aos-lock remove <absorbed-id>`, and let the absorbing capability's
   own upgrade render the replacements. Retired context-block markers
   (`aos:onboarding@…`, `aos:capability-builder@…`) come out in the same pass — the new
   blocks carry their own markers. `MOD.md` files never move on their own: if the absorbing
   capability's interview covers the same questions, offer the merge; otherwise leave the
   file and say it is now unused.
5. Report per capability: upstream changes taken, MOD statements re-applied, statements
   retired, anything folded in step a, any skill renamed or capability absorbed — and at
   most one promotion offer, if a fold qualified.
