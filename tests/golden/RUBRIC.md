# Render-equivalence rubric

Score each criterion `EQUIVALENT | DIVERGENT` with one line of evidence. Agentic renders
vary in wording; they must not vary in *facts*.

1. **Artifact set & placement** — same files in the same roles (skill per `used_by` scope,
   agent homes, cron jobs, zone registrations). Extra or missing artifacts = DIVERGENT.
2. **Every MOD nuance represented** — walk the fixture MOD's answers + body sentences;
   each must be honored somewhere in the render (sentinels are the deterministic subset;
   this criterion covers the prose beyond them).
3. **No upstream semantics dropped** — the shipped skill's rules all survive
   personalization (e.g. capture's five-second budget, drain's never-delete rule).
4. **Nothing invented** — no personalization that MOD.md doesn't license, no extra
   schedules, no unrequested config keys.
5. **Bookkeeping intact** — lockfile entries with hashes for every artifact, origin tags
   everywhere, `schedules_owned` matching reality.
