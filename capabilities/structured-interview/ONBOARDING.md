---
questions:
  - id: interview_surface
    prompt: Which conversational surface should interviews use?
    type: string
    required: true
  - id: interview_workspace
    prompt: Where should active and completed interview records live locally?
    type: path
    required: true
  - id: voice_mode
    prompt: Should questions default to voice, text, or mirror the user's latest message?
    type: enum
    required: true
  - id: kb_mode
    prompt: Should completed interviews be captured to a KB?
    type: enum
    required: true
  - id: kb_base
    prompt: What is the absolute KB path? Use an empty string when KB mode is disabled.
    type: string
    required: true
---

# Structured Interview onboarding

Ask only for missing answers. `interview_surface` is `cli` for a terminal or desktop session — where the session itself is the reply tuple and questions stay text-only whatever `voice_mode` says — or the name of the messaging surface the interview replies on, such as `telegram`. `voice_mode` is `voice`, `text`, or `mirror`; `kb_mode` is `configured` or `disabled`. `configured` requires a nonempty absolute `kb_base`; `disabled` requires `kb_base: ""`.
