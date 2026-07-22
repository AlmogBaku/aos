---
id: onboarding
version: 0.1.1
tags: [infra]
summary: The interview engine — reads a capability's ONBOARDING.md, interviews the user, and writes their MOD.md overlay; owns the global bootstrap interview.
skills:
  - id: interview
    used_by: [main]
---

# onboarding

The interview engine every capability's install invokes (ARCHITECTURE §3.2).

## Install narrative

Materialize one skill, `interview`, into the front agent. No agents, schedules, or KB
zones.

This capability's own `ONBOARDING.md` is the **global bootstrap interview** (BOOTSTRAP.md
step 2); it writes the root `MOD.md` every other transform reads. No dependencies — the
installer depends on *it*, so it installs first (with kb).

Re-runs ask only unanswered or `re_ask` questions; `--refresh` re-asks all and shows a
diff before writing. Nothing self-deletes (§3.2).
