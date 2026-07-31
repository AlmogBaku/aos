---
name: remove
description: "Removes an installed aos capability exactly, walking its lockfile entry backwards — jobs, symlinks, marker blocks, config keys, agents it created, its tool — and leaving the user's MOD.md in place so a re-install returns personalized. Use when the user says \"remove\", \"uninstall\", or \"get rid of\" and names an installed capability. Do NOT use to undo one setting or turn off a single schedule — that is capability-evolve — and not to retire something upstream, which is capability-contribute."
---

# capability-remove

Not in context yet? Load the `capability-lifecycle` skill first — the map, the
contract, and the Experience rules.

1. `aos-cap show <id>` → the entry: artifacts and links (including the
   capability's tool binary, recorded as an artifact), `schedules_owned`, config keys,
   env variable names, scripts.
2. Scope: removing the capability entirely, or *from one harness* while it
   stays installed elsewhere? **Per-harness removal**: run step 4 for that harness only
   and skip its render deletion (the render is shared — it stays), then re-`record` the
   reduced set (start from `aos-cap show`, drop that harness's links/artifacts/jobs,
   keep everything else), then step 6's verify scoped to that harness. The lockfile
   entry and the MOD file both stay. Skip step 5. Step 3's dependents check still applies **scoped to this harness** (a
   capability installed here that depends on this one). Note the lockfile's
   `schedules_owned` is a flat id list with no harness dimension (§5.5), so identify
   *this* harness's jobs by introspecting the harness, not by reading the lockfile.
   **Whole removal** continues below.
3. Dependents check: another entry in `aos-cap list` whose manifest
   `depends.capabilities` names this one → say so; stop unless the user insists (then
   remove dependents first).
4. Un-write per the cheat-sheet's Removal section (load
   the `capability-lifecycle` skill's `reference/harness-<harness-runtime>.md` now), in its
   stated order — typically: jobs →
   skill symlinks (delete the links; then delete **only** `personal/capabilities/<id>/skills/`
   **via a commit** — never the capability directory itself and never its `MOD.md` — revertible, the persist
   hook's dated message says why) → marker blocks → config keys → `.env` lines (ask
   first) → agents this capability created and nothing else uses → scripts/hooks →
   its tool (`uv tool uninstall`). A recorded link into `<home>/vendor` is a referenced
   third-party skill: unlink it, and offer to drop the vendor clone only if no other entry
   links into it.
   **Its machine-local state under `<home>/.aos/` is not in the lockfile, so nothing walks
   it backwards** — removing kb leaves `kb-principal.yml` behind. Offer to delete it, and
   say what it is: the list mapping this machine's human principals to their bases. It is
   the user's, not the capability's, so an unasked deletion loses an answer they gave; a
   re-install would otherwise adopt the old identity silently, which is right often enough
   to be worth asking about rather than guessing.
5. Tell the user their MOD.md stays: "your answers survive — in your personal repo,
   reinstalling brings it back personalized."
6. Verify: re-introspect until no `metadata.aos.origin`, `aos:` names, marker
   blocks, or links into `personal/` remain; `aos-cap remove <id>`; friendly close.
