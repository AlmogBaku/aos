---
name: remove
description: Removes an installed aos capability exactly, walking its lockfile entry backwards. Use when the user says "remove" or "uninstall" and names an installed capability.
---

# capability-remove

Not in context yet? Load the `capability-lifecycle` skill first — the map, the
contract, and the Experience rules.

1. **[D]** `aos-lock show <id>` → the entry: artifacts and links (including the
   capability's tool binary, recorded as an artifact), `schedules_owned`, config keys,
   env variable names, scripts.
2. **[D]** Scope: removing the capability entirely, or *from one harness* while it
   stays installed elsewhere? **Per-harness removal**: run step 4 for that harness only
   and skip its render deletion (the render is shared — it stays), then re-`record` the
   reduced set (start from `aos-lock show`, drop that harness's links/artifacts/jobs,
   keep everything else), then step 6's verify scoped to that harness. The lockfile
   entry and the MOD file both stay. Skip step 5. Step 3's dependents check still applies **scoped to this harness** (a
   capability installed here that depends on this one). Note the lockfile's
   `schedules_owned` is a flat id list with no harness dimension (§5.5), so identify
   *this* harness's jobs by introspecting the harness, not by reading the lockfile.
   **Whole removal** continues below.
3. **[D]** Dependents check: another entry in `aos-lock list` whose manifest
   `depends.capabilities` names this one → say so; stop unless the user insists (then
   remove dependents first).
4. **[A]** Un-write per the cheat-sheet's Removal section (load
   the `capability-lifecycle` skill's `reference/harness-<harness-runtime>.md` now), in its
   stated order — typically: jobs →
   skill symlinks (delete the links; then delete **only** `personal/capabilities/<id>/skills/`
   **via a commit** — never the capability directory itself and never its `MOD.md` — revertible, the persist
   hook's dated message says why) → marker blocks → config keys → `.env` lines (ask
   first) → agents this capability created and nothing else uses → scripts/hooks →
   its tool (`uv tool uninstall`). A recorded link into `<home>/vendor` is a referenced
   third-party skill: unlink it, and offer to drop the vendor clone only if no other entry
   links into it.
5. Tell the user their MOD.md stays: "your answers survive — in your personal repo,
   reinstalling brings it back personalized."
6. **[D]** Verify: re-introspect until no `metadata.aos.origin`, `aos:` names, marker
   blocks, or links into `personal/` remain; `aos-lock remove <id>`; friendly close.
