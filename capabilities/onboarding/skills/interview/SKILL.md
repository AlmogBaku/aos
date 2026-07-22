---
name: interview
description: Runs a capability's onboarding interview and writes the user's MOD.md overlay. Use when installing or re-onboarding any aos capability, when the user asks to redo/refresh their answers, or when bootstrapping the global MOD.md for a new user.
---

# interview

You are running an onboarding interview for one capability. The contract you are
implementing is ARCHITECTURE §3.1–3.2: typed answers → MOD.md frontmatter, prose nuance →
MOD.md body, secret values → the harness store (references only in MOD.md). You are the
**only** writer of MOD.md files.

## Inputs

- The target capability's `ONBOARDING.md`:
  - **frontmatter** — the typed question list. Each question: `id`, `prompt`, `type`
    (`string | number | boolean | enum | list | path`), optional `required`, `secret`,
    `re_ask` (booleans, default false).
  - **body** — the conversational script: tone, ordering, follow-ups, what good answers
    look like. Follow it; don't read questions off like a form.
- The existing `MOD.md` for this capability, if any (re-run case).
- The global root `MOD.md`, for context (skip questions whose answer is already implied
  globally — confirm instead of re-asking).

## Which questions to ask

| Situation | Ask |
|---|---|
| First run (no MOD.md) | every question; `required` ones must get an answer, others may be skipped |
| Re-run | only questions with no answer in MOD.md, plus every `re_ask: true` question |
| `--refresh` | every question again, current answer shown as the default |

Never delete an existing answer the user didn't change. Nothing self-deletes.

## Conducting the interview

Work through the body script conversationally — cluster related questions, accept "skip"
for anything not `required`, and capture *everything the user says beyond the typed answer*
as prose nuance for the body. The nuance is often worth more than the answer ("19:00 —
but never schedule over choir practice" → `19:00` is the answer; the rest is body prose).

## Writing MOD.md

After the conversation, before writing:

1. **Validate** every answer against its question — see [sections/answer-validation.md](sections/answer-validation.md).
2. **Secrets**: for every `secret: true` answer, write the value to the harness secret
   store per the cheat-sheet's Secrets section, and record only the reference in MOD.md.
   Never write a secret value into any markdown file, and never repeat it back in chat.
3. **Diff gate**: on re-run and `--refresh`, show the user a diff of the MOD.md changes
   and get approval before writing. On first run, show the drafted MOD.md.

MOD.md format (this skill is its normative definition):

```markdown
---
capability: <id>
onboarded_version: <capability version interviewed against>
answers:
  <question_id>: <typed value>
secrets:
  <question_id>: {store: <store>, key: <key>}
---

<prose nuance, organized under headings the transform can quote —
preferences, exceptions, red lines, phrasing the user actually used>
```

Location: the **root** `MOD.md` of the user's clone when interviewing for the global
bootstrap (the onboarding capability itself); `capabilities/<id>/MOD.md` for any other
capability. The overlay is user-owned — never commit it upstream, never edit shipped files.

Mechanics that keep re-runs no-ops:

- `onboarded_version` = the target capability's `CAPABILITY.md` `version` at interview time.
- **Never re-serialize unchanged content.** Unchanged answers and body text are preserved
  byte-for-byte; you edit the file, you don't regenerate it. (The re-run acceptance test
  diffs bytes.)
- **Empty diff ⇒ no write.** If a re-run or `--refresh` changes nothing, say so and touch
  nothing — there is no approval prompt for a diff with no changes.
- Body headings are emitted only when there is nuance under them — no empty sections.

## After writing

Report: which questions were answered, skipped, or unchanged; where secrets went (store
and key names only); and — on re-runs — the diff that was applied. If the interview was
part of an install, hand back to the installer (the transform reads what you just wrote).
