---
questions:
  - id: editorial_workspace
    prompt: Where should the ideas queue and in-development pieces live?
    type: path
    required: true
  - id: backlog_checker
    prompt: What is the absolute installed path of Ghostwriter's check_backlog.py script?
    type: path
    required: true
  - id: kb_base
    prompt: What is the absolute path of the KB Ghostwriter should search for source material?
    type: path
    required: true
  - id: content_channels
    prompt: Which output channels should Ghostwriter support?
    type: list
    required: true
  - id: voice_examples_path
    prompt: Where is the optional approved voice-example corpus, if one exists?
    type: path
  - id: source_interview_cron
    prompt: When should the weekly source interview start (5-field cron)?
    type: string
    required: true
  - id: source_interview_deliver
    prompt: 'Where should the interview job''s cron delivery go — "local" for silent (the desktop session is the delivery), or "origin" or "<platform>:<chat_id>" to also get a ping?'
    type: string
    required: true
  - id: editorial_session_cron
    prompt: When should the editorial queue or active piece resume (5-field cron)?
    type: string
    required: true
  - id: editorial_session_deliver
    prompt: 'Where should the editorial job''s cron delivery go — "local" for silent (the desktop session is the delivery), or "origin" or "<platform>:<chat_id>" to also get a ping?'
    type: string
    required: true
  - id: ideas_limit
    prompt: How many unprioritized ideas may stay active?
    type: number
    required: true
  - id: active_pieces_limit
    prompt: How many pieces may be developed concurrently?
    type: number
    required: true
  - id: idea_stale_days
    prompt: After how many untouched days should an idea leave the active queue?
    type: number
    required: true
  - id: piece_stale_days
    prompt: After how many untouched days should an in-development piece be parked?
    type: number
    required: true
---

# Ghostwriter onboarding

Defaults: Blog/LinkedIn/X; 10 ideas; 2 active pieces; ideas stale at 30 days, pieces at 14. With no voice corpus, critique preserves supplied vocabulary without inventing a verdict.

The two cron answers must never share a minute: both jobs take the one editorial-workspace lock, so a shared minute costs a run. Each job opens a titled desktop session the user answers there, so both `*_deliver` answers default to `local` — silent; `origin` or `<platform>:<chat_id>` also pings that a session is waiting.
