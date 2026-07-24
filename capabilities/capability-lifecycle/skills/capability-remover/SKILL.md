---
name: capability-remover
description: Removes an installed aos capability exactly, walking its lockfile entry backwards. Use when the user says "remove <capability>" or "uninstall <capability>".
---

# capability-remover

Not in context yet? Load the `capability-lifecycle` skill first — the map, the
contract, and the Experience rules.

1. **[D]** `aos-lock show <id>` → the entry: artifacts and links (including the
   capability's tool binary, recorded as an artifact), `schedules_owned`, config keys,
   env variable names, scripts.
2. **[D]** Dependents check: another entry in `aos-lock list` whose manifest
   `depends.capabilities` names this one → say so; stop unless the user insists (then
   remove dependents first).
3. **[A]** Un-write per the cheat-sheet's Removal section (load
   `harnesses/<harness-runtime>.md` now), in its stated order — typically: jobs →
   skill symlinks (delete the links; then delete the render dirs in
   `personal/capabilities/<id>/skills/` **via a commit** — revertible, the persist
   hook's dated message says why) → marker blocks → config keys → `.env` lines (ask
   first) → agents this capability created and nothing else uses → scripts/hooks →
   its tool (`uv tool uninstall`).
4. Tell the user their MOD.md stays: "your answers survive — in your personal repo,
   reinstalling brings it back personalized."
5. **[D]** Verify: re-introspect until no `x-aos-origin:`, `aos:` names, marker
   blocks, or links into `personal/` remain; `aos-lock remove <id>`; friendly close.
