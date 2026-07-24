---
name: capability-remover
description: Removes an installed aos capability exactly, walking its lockfile entry backwards. Use when the user says "remove <capability>" or "uninstall <capability>".
---

# capability-remover

Not in context yet? Load the `capability-lifecycle` skill first.

1. **[D]** `aos-lock show <id>` → the entry: artifacts, `schedules_owned`, config keys,
   env variable names, scripts, tool install.
2. **[D]** Dependents check: another entry in `aos-lock list` whose manifest
   `depends.capabilities` names this one → say so; stop unless the user insists (then
   remove dependents first).
3. **[A]** Un-write per the cheat-sheet's Removal section (load
   `harnesses/<harness-runtime>.md` now), in its stated order — typically: jobs →
   skills → marker blocks → config keys → `.env` lines (ask first) → agents this
   capability created and nothing else uses → scripts/hooks → its tool
   (`uv tool uninstall`).
4. Tell the user their MOD.md stays: "your answers survive — reinstalling brings it
   back personalized."
5. **[D]** Verify: re-introspect until no `x-aos-origin:`, `aos:` names, or marker
   blocks remain; `aos-lock remove <id>`; friendly close.
