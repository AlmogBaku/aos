---
id: <stable-id>
date: <YYYY-MM-DD>
status: active
completion_phase: null
capture_phase: null
capture_payload_sha256: null
objective: "<YAML-escaped one line>"
source_surface: "<surface>"
source_conversation_id: "<real-inbound-conversation-id>"
source_thread_id: "<thread-id-or-none>"
source_key: "<surface>|<real-inbound-conversation-id>|<thread-id-or-none>"
source_caller_id: "<stable-job-or-artifact-id-or-none>"
return_mode: <direct|poll-completed>
return_phase: <pending|ready-to-return|delivered>
delivered_at: null
delivered_to: null
current_question_id: Q1
next_action: await-answer
return_question_id: null
pending_operation: null
operation_target: null
completion_condition: null
kb_pending_path: null
capture_error: null
last_confirmed_turn: 0
started_at: <ISO-8601>
updated_at: <ISO-8601>
---

## Question plan

- Q1 [current]: <question> | useful_nugget: <signal> | evidence_needed: <none|target>
- Q2 [planned]: <question> | useful_nugget: <signal> | evidence_needed: <none|target>
- Q3 [planned]: <question> | useful_nugget: <signal> | evidence_needed: <none|target>

Allowed question statuses: `planned`, `current`, `answered`, `skipped`, `evidence-needed`.

## Transcript

### Turn 1 — interviewer

- question_id: Q1
- source_locator: <message-id-or-timestamp>

### Turn 2 — user

- source_locator: <message-id-or-timestamp>

## Nuggets

- text: <one sentence>
  turns: [2]

## Claims or decisions

## Open questions
