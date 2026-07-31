---
name: capability-upgrade
description: Upgrades installed aos capabilities by folding the user's uncaptured
  hand-edits into their MOD.md and re-applying it to fresh upstream, diff-gated, one
  reviewable commit per render. Use when the user says "update" or "upgrade" — the
  whole kit or one capability — or after a git pull of the aos upstream clone. Do
  NOT use for a capability that is not installed yet (that is capability-install)
  or to change what a capability does for this user (capability-evolve); this skill
  preserves existing personalization rather than adding any.
metadata:
  aos:
    origin: capability-lifecycle@0.3.5
---
# capability-upgrade

Not in context yet? Load the `capability-lifecycle` skill first — the map, the
contract, the overlay doctrine, and the Experience rules. The model: **MOD.md states
the user's deltas; upgrade = re-apply them to fresh upstream, into `personal/`'s
working tree.**
The current install is a drift source, never a merge input; the review gate is a git
diff in the user's own repo.

1. Scope: the named capability, else every entry in `aos-cap list`.
2. Kit-wide: pull `<home>/upstream` from the canonical remote (`git pull
   upstream main` when an `upstream` remote exists, else `git pull`) — it cannot touch
   `personal/`, a different repo. On a non-`main` branch (a contributor dogfooding a
   change, or a self-drafted cheat-sheet branch): skip the pull, say so, name the
   branch, and say how to resume upstream updates
   (`git -C <home>/upstream switch main`). A capability
   needs work when its manifest version (`aos-cap manifest`) ≠ its lockfile version.
   Migration note: overlay files found *inside* the clone (a pre-household install) →
   offer the one-time move into `personal/` before anything else. Referenced third-party
   skills come along: for each recorded link into `<home>/vendor`, `git -C <vendor-clone>
   pull --ff-only` (or the harness's plugin update), then re-`record` so the hashes match.
   Offline or a dirty clone → say so and continue; a stale reference is never a blocker.
3. Per capability needing work:
   a. `aos-cap verify <id>` — two classes, two responses. *Artifact drift*
      (a render file's hash changed = the user's hand-edit) → fold each into
      MOD.md first per the `capability-lifecycle` skill's `reference/overlay.md` (edit the
      statement that covers it — never
      append a contradicting one) ("you changed X — keeping it").
      *Link damage* (`MISSING LINK`, `NOT A LINK (copies are banned)`, `RELINKED`,
      `DANGLING LINK`) is not a hand-edit and never folds: re-create the link from the
      lockfile's recorded target, say what you repaired, and stop if the target itself
      is gone (that is a broken install, not an upgrade). A
      fold that reaches beyond the `{{mod}}` slots is mechanism-shaped — note it for
      the promotion judgment (overlay.md, Promote and retire), end of conversation.
   b. Name gate: `aos-cap --home <home> skills <dir> --check --harness-skills
      <each skills dir this harness reads>`. Upstream may have renamed or added a skill, so the installed
      names can differ from the recorded links — a rename means link the new name and drop
      the old one in step d. Exit 17 → stop and report; never rename locally. This
      capability's own links are exempt, so a plain re-render is always clean. If it ships
      `agents/`, gate those too in the same breath: `aos-cap --home <home> agents <dir>
      --check` — same flat namespace, same exit 17, same never-rename-locally. It checks
      two of three sources and names the third (agents already in the harness — no
      enumeration yet) in capitals.
   c. **First, before `--force` touches anything**: `git -C <home>/personal status
      --porcelain -- capabilities/<id>`. `--force` re-render is `rmtree` then `copytree`, so a
      pre-existing **untracked** file of the user's under that directory is gone with no commit
      to recover it from — and `aos-cap verify` cannot warn you, because it is add-blind (an
      extra file inside a recorded render reports `clean`). Name any `??` entry to the user and
      get a decision before proceeding; a tracked file is safe (the diff in step d shows it).
      Then re-render: `aos-cap render <dir> <skill-id> --out
      <home>/personal/capabilities/<id>/skills --force` per declared skill, then fresh
      upstream × MOD.md — the same transform as install (`reference/overlay.md`), written
      into `personal/`'s working tree; interview only new or `re_ask` questions. A skill
      whose installed name changed leaves its old render directory behind: delete it in the
      same commit, so the diff shows the rename as one move. Then STAGE any native-plan
      changes per the cheat-sheet (load it now if not in context).
   d. GATE: stage this capability, then diff it — `git -C <home>/personal add
      -A -- capabilities/<id>` then `git -C <home>/personal diff --staged --
      capabilities/<id>` — the old render vs the new, per file, **including files the
      re-render added** (a bare `git diff` hides them) — plus the native plan. Approve
      → commit (dated message). Decline → `git -C <home>/personal restore --staged
      --worktree -- capabilities/<id>`, then `git -C <home>/personal clean -fd --
      capabilities/<id>` as belt-and-braces (restore already removes the staged
      additions; clean catches anything staging missed), stop. Keep every command
      path-scoped: unscoped staging or resetting would capture — or destroy —
      unrelated work elsewhere in `personal/`. (The untracked-file check is step c's, because
      by this point `--force` has already run — a warning here would name a file that no
      longer exists.)
   e. **Re-install the capability's own tool if it ships one**, before recording:
      `uv tool install --force --from <dir>/tool <package>`. Nothing else in this flow updates
      a binary, and `uv` will otherwise serve whatever it has cached — so an upgrade that
      re-renders every skill can leave the executable those skills call several versions
      behind, with the prose describing behaviour the binary does not have. `--force` is what
      makes it re-resolve; the version in the tool's `pyproject.toml` tracks the capability's,
      so a bumped capability is a bumped package.
   f. EXECUTE the native plan (links usually survive re-render untouched —
      verify, don't assume); `aos-cap record <id>` with the full updated set (start
      from `aos-cap show` — `record` replaces the entry wholesale, never call it with
      a partial list; keep `--source-root` and `--link` records).
   g. Retirement pass (overlay.md, Promote and retire): fresh upstream now
      covers a MOD statement — a new interview question over its subject, or the
      behavior baked in → offer to retire it (diff-shown; written only through
      capability-evolve).
4. **Absorbed capabilities.** A lockfile entry whose capability no longer exists upstream
   was folded into another one (0.3.0 absorbed `onboarding`, `importer`, and
   `capability-builder` into `capability-lifecycle`). Say what happened, then: unlink that
   entry's skill links, `aos-cap remove <absorbed-id>`, and let the absorbing capability's
   own upgrade render the replacements. Retired context-block markers
   (`aos:onboarding@…`, `aos:capability-builder@…`) come out in the same pass — the
   mode-boundary block carries its own marker. A pre-0.3.0 install also has an identity
   block distilled from the global MOD: remove it, say why (the harness owns user context;
   `MOD.md` remains the authoritative store), and write nothing in its place. `MOD.md` files never move on their own: if the absorbing
   capability's interview covers the same questions, offer the merge; otherwise leave the
   file and say it is now unused.
5. Report per capability: upstream changes taken, MOD statements re-applied, statements
   retired, anything folded in step a, any skill renamed or capability absorbed — and at
   most one promotion offer, if a fold qualified.
