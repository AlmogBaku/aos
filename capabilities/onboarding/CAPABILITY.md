---
id: onboarding
version: 0.1.0
tags: [infra]
summary: The interview engine — reads a capability's ONBOARDING.md, interviews the user, and writes their MOD.md overlay; owns the global bootstrap interview.
skills:
  - id: interview
    used_by: [main]
---

# onboarding

The interview engine every capability's install invokes (ARCHITECTURE §3.2). It exists so
that no capability ever ships with a blank page: install-time personalization is a
conversation, and the answers land in exactly one durable place — the user's `MOD.md`
overlay.

## Install narrative

Installing this capability materializes one skill, `interview`, into the front agent
(`used_by: [main]`). There are no agents, schedules, or KB zones.

This capability also carries the **global bootstrap interview** in its own `ONBOARDING.md`:
identity, timezone, working hours, sacred time, red lines. Running it is step 2 of
`docs/BOOTSTRAP.md` and writes the **root** `MOD.md` — the global overlay every other
capability's transform reads. That is why onboarding has no dependencies and must install
first (together with kb): the installer depends on *it*.

Re-running an interview is always safe: the engine asks only unanswered or
`re_ask`-flagged questions, and a full `--refresh` shows a diff before writing anything
(§3.2 — interviews are re-runnable and diffable; nothing self-deletes).
