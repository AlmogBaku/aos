---
name: upgrade
description: "Upgrades installed aos capabilities by folding the user's uncaptured hand-edits into their MOD.md and re-applying it to fresh upstream, diff-gated before each render goes live. Use when the user says \"update\" or \"upgrade\" — the whole kit or one capability — or after a git pull of the aos upstream clone. Do NOT use for a capability that is not installed yet (that is capability-install) or to change what a capability does for this user (capability-evolve); this skill preserves existing personalization rather than adding any."
---

# capability-upgrade

Not in context yet? Load the `capability-lifecycle` skill first — the map, the
contract, the overlay doctrine, and the Experience rules. The model: **MOD.md states
the user's deltas; upgrade = re-apply them to fresh upstream, into
`<aos_home>/rendered/.staging/<id>/`.**
The current install is a drift source, never a merge input; the review gate is a diff of
the live render against the staged one, and only `aos-cap swap` puts a render live.

1. Scope: the named capability, else every entry in `aos-cap list`.
2. Kit-wide: pull `<aos_home>/upstream` from the canonical remote (`git pull
   upstream main` when an `upstream` remote exists, else `git pull`) — it cannot touch
   `personal/`, a different repo. On a non-`main` branch (a contributor dogfooding a
   change, or a self-drafted cheat-sheet branch): skip the pull, say so, name the
   branch, and say how to resume upstream updates
   (`git -C <aos_home>/upstream switch main`). A capability
   needs work when its manifest version (`aos-cap manifest`) ≠ its lockfile version.
   Migration note: overlay files found *inside* the clone (a pre-household install) →
   offer the one-time move into `personal/` before anything else. Referenced third-party
   skills come along: for each recorded link into `<aos_home>/vendor`, `git -C <vendor-clone>
   pull --ff-only` (or the harness's plugin update), then re-`record` so the hashes match.
   Offline or a dirty clone → say so and continue; a stale reference is never a blocker.
   **Renders still in `personal/`** (a household from before capability-lifecycle 0.7.0:
   `aos-cap migrate rendered` lists moves) → upgrade `capability-lifecycle` alone first,
   with the skill you have, then reload this skill and run the migration before anything
   else — every later render goes to `rendered/`, and the tool refuses an `--out` under
   `personal/`:
   1. **Plan.** `aos-cap migrate rendered --scan <harness home>…` with each harness home
      and each `--ignore` glob of its skip list the cheat-sheet names. It writes nothing
      but its state — the scan set and the old renders — which the next two steps read. Show the user the whole plan —
      moves, link re-points, the text the copy rewrites, drift, outside references — and
      get approval. Fold any drift first (step 3a); `--apply` refuses while any remains.
      A recorded link that is missing or re-pointed may be the user's own change — a skill
      taken back from a profile others can reach. Ask before re-creating it; the other fix
      is to re-record the entry without it.
   2. **Apply.** First pause any agent whose hook compares paths (a command wall), and
      wait out a live guest session on it: between this step and the hook switch, its
      walls would refuse legitimate work. Then `aos-cap migrate rendered --apply`. It copies
      each render, re-points every link and rewrites the lockfile. The old renders stay in
      place, so every old path still resolves.
   3. **Fix each outside reference through its owner.** A `MOD.md` answer goes through
      {{skill: evolve}}. One of the user's own packages that bakes the path gets the edit in
      its source, then a re-render through staging and the gate. A harness file is changed
      through the cheat-sheet's steps — its CLI, and only the consent file it names. A hook
      is its own gate: show the user the old and new exact command and the approval you
      will write, and wait. Then re-approve it by its new exact command before the config
      points at it, check it, and revoke the old approval (the cheat-sheet's order). Change
      hooks last, once their scripts are final.
   4. **Prove the gates before anything old goes.** Run every security plugin's and
      wall's own synthetic check against the new copies. Restart the harness, with the
      user's go-ahead, once its work is idle, and confirm each plugin loaded from its
      re-pointed link (the cheat-sheet's check). On any failure, re-point that link back:
      its old render is still there.
   5. **Finish.** `aos-cap migrate rendered --finish` refuses while anything still names
      an old render path or links into one, and otherwise sends the old renders to the
      trash. Resume what you paused, then commit `personal/` (dated message) — the
      renders' removal from it is that commit.
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
   b. Name gate: `aos-cap --home <aos_home> skills <dir> --check --harness-skills <dir> …`
      (one `--harness-skills` per skills dir this harness reads). Upstream may have renamed or added a skill, so the installed
      names can differ from the recorded links — a rename means link the new name and drop
      the old one in step d. Exit 17 → stop and report; never rename locally. This
      capability's own links are exempt, so a plain re-render is always clean. If it ships
      `agents/`, gate those too in the same breath: `aos-cap --home <aos_home> agents <dir>
      --check` — same flat namespace, same exit 17, same never-rename-locally. It checks
      two of three sources and names the third (agents already in the harness — no
      enumeration yet) in capitals.
   c. **Re-render into staging.** A `.staging/<id>` left by an abandoned gate goes first:
      `aos-cap discard <id>`. Then `aos-cap render <dir> <skill-id> --out
      <aos_home>/rendered/.staging/<id>/skills` per declared skill, plus any other subtree the
      briefing pins (`adapters/`, say, leaving `__pycache__` and `*.pyc` behind). Then apply fresh upstream × this capability's MOD.md
      (the `capability-lifecycle` skill's `reference/overlay.md`, Which MOD.md) — the same
      transform as install, household rules included — to the staged copy. Interview only
      new or `re_ask` questions. A household path you bake names `rendered/<id>/`, never
      `.staging/`. A skill whose installed name changed is simply absent from the staged
      tree, and the gate shows it as removed. Then STAGE any native-plan changes per the
      cheat-sheet (load it now if not in context).
   d. GATE: `diff -ruN -x __pycache__ -x '*.pyc' <aos_home>/rendered/<id>
      <aos_home>/rendered/.staging/<id>` — the live render against the staged one, per
      file. It shows files the re-render added and files it dropped, including any file
      the user added by hand inside the live render. Bytecode is left out: a live render
      grows it as it runs. Show it with the native plan. Approve → `aos-cap swap <id>`: the
      staged render goes live and the old one goes to the OS trash. Decline →
      `aos-cap discard <id>`, and stop; the live render is untouched.
   e. **Re-install the capability's own tool if it ships one**, before recording:
      `uv tool install --force --from <dir>/tool <package>`. Nothing else in this flow updates
      a binary, and `uv` will otherwise serve whatever it has cached — so an upgrade that
      re-renders every skill can leave the executable those skills call several versions
      behind, with the prose describing behaviour the binary does not have. `--force` is what
      makes it re-resolve; the version in the tool's `pyproject.toml` tracks the capability's,
      so a bumped capability is a bumped package.
   f. **Reconcile links, then EXECUTE.** Compare the entry's recorded `links` and
      `uses_links` with what the fresh manifest declares — each skill's `used_by`, each
      `uses` row — plus any link a MOD statement sanctions (a household rule linking skills
      into every capability agent, say). Declared but missing → stage it. Recorded but not
      declared → show it and ask; **never drop or move a link silently** — that is how a
      provider's upgrade once broke a consumer for weeks. Another entry's `uses_links` into
      this capability's render are that entry's: never touch them. A link this entry
      records that another capability's `uses` now declares moves to that capability:
      re-record this entry without it first, then the other with `--uses-link` (exit 19
      enforces the order). Then EXECUTE the native plan (links survive a swap
      untouched, because the path is the same — verify, don't assume); a hook whose command or script changed must be
      re-approved and re-verified per the cheat-sheet — the consent was for the old one.
      `aos-cap record <id>` with the full updated set
      (start from `aos-cap show` — `record` replaces the entry wholesale, never call it
      with a partial list; keep `--source-root`, `--link` and `--uses-link` records), then
      `aos-cap verify` with no argument, so a link another entry depends on is checked
      too.
   g. Retirement pass (overlay.md, Promote and retire): fresh upstream now
      covers a MOD statement — a new interview question over its subject, or the
      behavior baked in → offer to retire it (diff-shown; written only through
      {{skill: evolve}}).
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
