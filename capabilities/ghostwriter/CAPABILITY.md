---
id: ghostwriter
version: 0.3.0
tags: [usecase]
summary: Interview-driven editorial workflow from grounded ideas to manually published Blog, LinkedIn, and X content.
depends:
  capabilities: [kb, capability-lifecycle, structured-interview, open-session]
  host:
    cron: preferred
    messaging.inbound: optional
    messaging.outbound: optional
uses:
  - {capability: open-session, skill: open-session, agents: [ghostwriter]}
  - {capability: structured-interview, skill: structured-interview, agents: [ghostwriter]}
skill_prefix: ghostwriter-
skills:
  - id: ghostwriter
    used_by: [ghostwriter]
  - id: ingest
    used_by: [ghostwriter]
  - id: develop
    used_by: [ghostwriter]
  - id: critique
    used_by: [ghostwriter]
  - id: repurpose
    used_by: [ghostwriter]
schedules:
  - id: source-interview
    cron: "0 10 * * 0"
    agent: ghostwriter
    prompt_ref: schedules/source-interview.md
    degraded: manual
  - id: editorial-session
    cron: "0 10 * * 2"
    agent: ghostwriter
    prompt_ref: schedules/editorial-session.md
    degraded: manual
  - id: develop-ahead
    cron: "15 9 * * 1,4"
    agent: ghostwriter
    prompt_ref: schedules/develop-ahead.md
    degraded: skip
---

# ghostwriter — installer's briefing

A focused editorial system for people who have source material but never turn it into finished content. Everything runs in its own `ghostwriter` agent (`agents/ghostwriter.agent.yaml`): the five skills, both schedules, and the `uses` links for `open-session` and `structured-interview`. Materialize the skills and configure the workspace from `ONBOARDING.md` / `MOD.md`. Needs capability-lifecycle 0.4.0 or later, for `uses`.

On Hermes, an existing `ghostwriter` profile is adopted with all its state — workspace, sessions, gateway, a hand-written `SOUL.md` — never re-created and never deleted on remove; `purpose` becomes `SOUL.md` only when the profile is created. Keep the `skills`, `terminal`, `file` and `clarify` toolsets enabled: the skills run the backlog checker through the terminal, and the interview offers choices through `clarify`.

The two chat schedules — `source-interview` (sourcing) and `editorial-session` (developing) — are cron agents whose only job is to use `open-session` to open one new titled session in the user's desktop, seeded with the prompt the schedule carries — the conversation happens there, on the user's time. So wire each of them with **only** the installed `open-session` skill attached; the conversation's own skills (interview, ingest, develop, critique, repurpose) are named in the schedule prompt and passed in the opening request, deliberately.

`develop-ahead` is different: an unattended run between chats that opens no session and talks to nobody. It moves work one gated step forward so the next chat has something to decide on. Wire it with the `ghostwriter`, `ghostwriter-ingest` and `ghostwriter-develop` skills and always deliver `local`. All three jobs read and rewrite the workspace `HANDOFF.md`, which is how every chat picks up from the last spot.

The installer substitutes every `{{skill: …}}` and `{{mod: …}}` slot in `schedules/*.md` before `cron create` — an unsubstituted slot is an install error. The `*_cron` MOD answers override the manifest's `cron:` values (`develop_ahead_cron` for the background run); `*_deliver` is a notification only (`local` is silent), and publishing stays manual.
