---
x-aos-origin: onboarding@0.2.0
name: onboarding
description: Runs a capability's onboarding interview and writes the user's MOD.md overlay. Use when installing or re-onboarding any aos capability, when the user asks to redo/refresh their answers, or when bootstrapping the global MOD.md for a new user.
---

# onboarding

You are the only writer of MOD.md files. Typed answers → frontmatter; prose nuance →
body; secret values → harness store (references only in MOD.md).

## Inputs

- Target capability's `ONBOARDING.md`: frontmatter = typed questions (`id`, `prompt`,
  `type: string|number|boolean|enum|list|path`, optional `required`/`secret`/`re_ask`
  booleans); body = the conversational script. Follow the script — don't read questions
  off like a form.
- Existing MOD.md for this capability, if any.
- Global root MOD.md — skip questions it already answers; confirm instead of re-asking.

## Which questions to ask

| Situation | Ask |
|---|---|
| First run | all; `required` must get answers, others may be skipped |
| Re-run | unanswered + every `re_ask: true` |
| `--refresh` | all, current answer shown as default |

Never delete an answer the user didn't change.

## Conduct

Cluster related questions; accept "skip" for non-required. Everything the user says
beyond the typed answer is body-prose nuance ("19:00 — but never over choir practice":
`19:00` is the answer, the rest is nuance).

## Write

1. Validate every answer per [reference/answer-validation.md](reference/answer-validation.md).
2. `secret: true` answers: value → harness store per the cheat-sheet; MOD.md gets only
   `{store, key}`. Never write or repeat the value.
3. Diff gate: show the diff (or the full draft on first run) and get approval.
   **Empty diff ⇒ no write, no prompt.**

Format (normative):

```markdown
---
capability: <id>
onboarded_version: <CAPABILITY.md version at interview time>
answers:
  <question_id>: <typed value>
secrets:
  <question_id>: {store: <store>, key: <key>}
---

<prose nuance under headings; omit headings with nothing under them>
```

Location: root `MOD.md` for the global bootstrap (this capability's own interview);
`capabilities/<id>/MOD.md` otherwise. Never re-serialize unchanged content — edit the
file, don't regenerate it (unchanged answers stay byte-identical).

## Report

Answered / skipped / unchanged; secret store+key names only; the applied diff on re-runs.
If part of an install, hand back to the installer.
