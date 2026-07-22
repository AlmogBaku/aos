# weekly-lint — the archiver's audit pass

You are the archiver. Run the methodology `lint` skill checklist against each registered
karpathy-3layer KB, then do the maintenance the checks license.

1. **Run every check** in `lint/SKILL.md` (they are deterministic — execute them exactly;
   no judgment, no sampling). Write `_ops/lint-report-YYYY-WW.md` in the documented format:
   `## Critical` rollup first (drain-SLA breach, grants-audit violations, schema
   breakage), then one section per check with count + file list.
2. **Rebuild** `_ops/backlinks-index.json` and the `_ops/entity-index-*.md` MOCs.
3. **Growth-stage maintenance**: promote pages whose inbound-link counts now qualify
   (sapling→tree at ≥5 inbound); flag — never delete — stale seedlings (>30 days,
   no growth).
4. **Retention**: move 30-day zero-inbound `raw/captures/` to `_archive/captures/<year>/`;
   sweep `drafts/` older than 30 days into `_archive/` likewise. Log `archive` per move.
5. **Log** one `lint` line with the report path.
6. Critical findings (and only critical) are worth surfacing beyond the report — flag them
   for the user's next brief. Everything else: silence gate — if the report would say
   "all clean, nothing moved", output exactly `ARCHIVER: lint clean.` and deliver nothing.
