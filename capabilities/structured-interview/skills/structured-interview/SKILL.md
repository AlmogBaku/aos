---
name: structured-interview
description: Conducts concise, resumable interviews and preserves source-linked InterviewRecords. Use when starting, continuing, or resuming an interview; when the user says "interview me", answers an active interview question, or a workflow needs source-grounded thoughts, decisions, examples, or open questions. Does not draft, edit, publish, or act on what an interview produced — it returns the record to its caller and stops.
---

# Structured Interview

Listen for what matters to the objective. One useful question beats a questionnaire.

## Start

1. State the objective in one line.
2. Use only `{{mod: interview_workspace}}/active/` and `completed/`; create both if absent. Identify the reply tuple: `source_surface`, the real inbound `source_conversation_id`, and `source_thread_id` or literal `none`; persist `source_key: <surface>|<conversation-id>|<thread-id>`. A scheduled caller also persists its exact job ID as `source_caller_id`, but never substitutes that synthetic ID for the reply tuple. On a CLI or desktop chat session the reply tuple is the session itself: `source_surface: cli`, `source_conversation_id` is that session's own id (the Session ID shown in the system prompt, else the harness's session-id environment variable — on Hermes, `HERMES_SESSION_ID`), `source_thread_id: none`, so `source_key: cli|<session-id>|none`. That is a real tuple, not a synthetic one, so it satisfies the next rule instead of triggering it. If the actual reply tuple is unavailable, stop before sending because the answer cannot be correlated safely.
3. A direct retry/resume first checks `completed/` for exactly one `return_mode: direct`, `return_phase: ready-to-return` record matching the full tuple and objective/caller identity; re-return it idempotently. The caller's next non-retry instruction acknowledges that return: atomically mark it delivered before continuing, so an explicit new start can proceed. Otherwise match `active/` by full tuple: one resumes, multiple stop with candidate IDs, zero creates. When the caller supplies a `source_caller_id`, also scan `active/` for records with that caller id and a different tuple: exactly one ⇒ surface it and offer resume or fresh, never auto-resume and never rebind silently; multiple ⇒ stop with candidate IDs. Build `<short-source-id>` as the first 12 lowercase hex characters of SHA-256 over UTF-8 `source_key`. Use `YYYY-MM-DD-<objective-slug>-<short-source-id>.md`, collision suffixes, parent confinement, and final stem as `id`. Build the complete file in a unique sibling temp, fsync it, then hard-link it no-replace to the chosen active path and unlink the temp; on collision restart matching/allocation. Subsequent checkpoints use temp+fsync+atomic replace. The slug is NFKD-normalized lowercase ASCII `a-z0-9` with separator runs collapsed to hyphens; fallback `interview`. YAML-serialize free text.
4. Sketch 3–6 likely questions, what would count as a useful nugget, and unknowns requiring evidence rather than conversation. Persist the plan with question IDs, mark the current question, and set `next_action: await-answer` before sending anything.
5. Ask the current question and wait.

## Each answer

1. Read for the real message, not only literal words. Reflect once only when it verifies understanding or sharpens the point.
2. Choose one: follow a relevant nugget; ask one correctness clarification; record `I don't know` as an open question and move on; retrieve evidence, inspect an artifact, or build a prototype; move to the next core question; or stop when the objective is met.
3. Before external evidence work, checkpoint one of `next_action: retrieve-evidence`, `inspect-artifact`, or `prototype` with `pending_operation`, target, completion condition, and `return_question_id`. On success, record the result, clear those fields, set `next_action: resume-question`, then return to that question. On failure, retain the checkpoint and surface the blocker.
4. Record the answer's source locator. Update transcript, `last_confirmed_turn`, question-plan status, cursor, `next_action`, and `updated_at` before asking again.

Do not dig into every detail. Do not repeat answered questions. A short interview and zero nuggets are valid outcomes.

## Question types

- **Open exploration:** ask plainly, one question at a time.
- **Closed factual check:** ask briefly; a tool is optional.
- **Choice between options:** explain concrete tradeoffs, then use the harness's `AskUserQuestion` equivalent.

For a non-interactive scheduled run or harness without that tool, persist numbered options and `next_action: await-choice`, deliver them to the persisted reply tuple, and wait for a reply on that same tuple. Never hide options only in prose, guess a choice, or rely on an unstated scheduler-session attachment.

Use `{{mod: voice_mode}}` on `{{mod: interview_surface}}`: `mirror` follows the latest inbound user modality when known, otherwise text. On a `cli` surface, text only — no voice regardless of `{{mod: voice_mode}}`. In voice mode, send one short voice question with no duplicate text. If voice delivery or TTS is unavailable, send one concise text question and record `voice_fallback: text` in the turn.

## Golden nuggets

Follow an answer when it contains objective-relevant experience, evidence, tension, mechanism, decision, or unusually precise language. Otherwise move on.

## Complete

1. Preserve the raw transcript. Fill only supported nuggets, claims/decisions, and open questions; every nugget cites turn IDs.
2. Make content terminal: set `status: complete`, `completion_phase: complete`, `next_action: finalize-capture`, and `updated_at`. Build one immutable canonical capture payload as UTF-8 JSON with keys `id`, `objective`, `source_surface`, `source_conversation_id`, `source_thread_id`, `source_caller_id`, `transcript`, `nuggets`, `claims_decisions`, and `open_questions`, serialized with sorted keys, compact separators, Unicode preserved, and one trailing newline. Exclude all capture/delivery fields and persist its SHA-256 as `capture_payload_sha256` before capture.
3. If `{{mod: kb_mode}}` is `disabled`, require rendered `kb_base` to be empty, set `capture_phase: skipped` and `kb_pending_path: null`, then continue at step 5. If configured, require a nonempty absolute `{{mod: kb_base}}`, set `capture_phase: capturing`, and invoke exact argv values: title `Interview — <objective> [<id>]`, source `<source_surface>:interview`, and the canonical payload via a file or stdin. Never interpolate shell text.
4. Save either `captured:` or `duplicate: matches` as `kb_pending_path`. Resolve a relative locator under canonical `kb_base`, reject absolute/escaping paths, and read it whether under `.kb/pending/` or `_raw/`. Verify its `source_sha256` and body equal the persisted canonical payload; never mutate KB content. On retry, submit the same payload so KB dedup returns the stable pending/raw locator. Persist failures in `capture_error`; verified recovery clears it and sets `capture_phase: complete`.
5. Preserve `skipped` or verified `complete`, set `next_action: none`, and perform the existing no-replace active→completed link/unlink transaction with its same-inode retry recovery. Return the completed path. Direct mode uses `ready-to-return`; scheduled mode uses `pending` until acceptance.

Return `status`, `record_path`, `record_id`, `source_caller_id`, `kb_pending_path`, and `capture_error`. Do not dump the record unless asked.

## Resume

Apply Start step 3's completed-direct recovery, then match the full source tuple across active records. Load the persisted cursor and perform `next_action`. `resume-question` returns to `return_question_id`; evidence actions execute their checkpoint; `await-choice` waits; `finalize-capture` continues from `capture_phase`. Never reconstruct state from memory.
