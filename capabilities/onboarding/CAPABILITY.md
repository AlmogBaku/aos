---
id: onboarding
version: 0.2.0
tags: [infra]
summary: The interview engine — reads a capability's ONBOARDING.md, interviews the user, and writes their MOD.md overlay; owns the global bootstrap interview.
skills:
  - id: onboarding
    used_by: [main]
---

# onboarding — installer's briefing

*(This document is consumed at install and not used afterwards. The runtime face of
the capability is the `onboarding` entry skill.)*

## What this is

The interview engine every capability's install invokes (ARCHITECTURE §3.2): it reads
a capability's `ONBOARDING.md` (typed questions in frontmatter, conversational script
in the body), interviews the user, and writes the `MOD.md` overlay (typed answers in
frontmatter, prose nuance in the body, secrets as `{store, key}` references). Its own
`ONBOARDING.md` doubles as the **global bootstrap interview** — identity, timezone,
working hours, sacred time, red lines — writing the root `MOD.md` every other
transform reads.

## What you materialize, and why

1. **The `onboarding` entry skill** — the whole capability: one skill, no narrower
   siblings. It goes to the front agent only; no agents, schedules, or KB zones.
2. **No dependencies — installs first, alongside `kb`.** Every other capability's
   install narrative calls back into this one; this one calls into nothing, so it and
   `kb` are the two things BOOTSTRAP.md brings up before anything else.

## Contracts to preserve

- Re-runs ask only unanswered or `re_ask` questions; `--refresh` re-asks all and shows
  a diff before writing. Nothing self-deletes (§3.2).
- Only this capability's skill writes MOD.md files; secret values live in the harness
  store, never inline.
