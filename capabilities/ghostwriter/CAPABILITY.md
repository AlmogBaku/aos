---
id: ghostwriter
version: 0.1.3
tags: [usecase]
summary: Interview-driven editorial workflow from grounded ideas to manually published Blog, LinkedIn, and X content.
depends:
  capabilities: [kb, capability-lifecycle, structured-interview, open-session]
  host:
    cron: preferred
    messaging.inbound: optional
    messaging.outbound: optional
skill_prefix: ghostwriter-
skills:
  - id: ghostwriter
    used_by: [main]
  - id: ingest
    used_by: [main]
  - id: develop
    used_by: [main]
  - id: critique
    used_by: [main]
  - id: repurpose
    used_by: [main]
schedules:
  - id: source-interview
    cron: "0 10 * * 1,4"
    agent: main
    prompt_ref: schedules/source-interview.md
    degraded: manual
  - id: editorial-session
    cron: "0 14 * * 3,4"
    agent: main
    prompt_ref: schedules/editorial-session.md
    degraded: manual
---

# ghostwriter — installer's briefing

A focused editorial system for people who have source material but never turn it into finished content. Install into a dedicated front profile alongside `structured-interview` and `kb`; materialize the five skills and configure the workspace from `ONBOARDING.md` / `MOD.md`.

Both schedules are cron agents whose only job is to use `open-session` to open one new titled session in the user's desktop, seeded with the prompt the schedule carries — the conversation happens there, on the user's time. So wire each job with **only** the installed `open-session` skill attached; the conversation's own skills (interview, ingest, develop, critique, repurpose) are named in the schedule prompt and passed in the opening request, deliberately.

Contested core is RFC-009, stated rather than worked around. Every skill here declares `used_by: [main]` and nothing in this manifest names a foreign agent — but ghostwriter installs into its **own** front profile, so the `main` this capability means is that profile's agent, and the `structured-interview`, `open-session` and `kb` skills its jobs and its opened sessions depend on reach that agent only because the install links their renders into this profile. That is the "my agent needs your skill" case no manifest field can express: the composition is real, the attachment is an install act rather than a declaration, and the schedule prompts name the opened session's skills as `{{skill: …}}` slots instead of claiming them in `used_by`. Every skill being scoped to `main` is therefore deliberate, not an oversight.

The installer substitutes every `{{skill: …}}` and `{{mod: …}}` slot in `schedules/*.md` before `cron create` — an unsubstituted slot is an install error. The `*_cron` MOD answers override the manifest's `cron:` values; `*_deliver` is a notification only (`local` is silent), and publishing stays manual.
