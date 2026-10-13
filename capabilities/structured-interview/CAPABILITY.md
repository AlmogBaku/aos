---
id: structured-interview
version: 0.1.4
tags: [usecase]
summary: Concise, resumable interviews that listen for objective-relevant nuggets and preserve a source-linked InterviewRecord.
depends:
  capabilities: [capability-lifecycle]
  host:
    messaging.inbound: preferred
    messaging.outbound: preferred
    voice.stt: preferred
    voice.tts: preferred
skills:
  - id: structured-interview
    used_by: [main]
---

# structured-interview — installer's briefing

A reusable interview path for manual or capability-driven interviews. It owns question craft, turn-taking, stopping, resumability, and the InterviewRecord. It does not own any downstream content or business workflow.

Link its entry skill per `used_by`; a capability whose own agent conducts the interview declares `uses` for it and owns that link. `ONBOARDING.md` and `MOD.md` configure the user's surface and communication preferences. Interview artifacts are captured through the existing `kb` command when configured; without KB, the skill returns the complete record contract to its caller for storage.
