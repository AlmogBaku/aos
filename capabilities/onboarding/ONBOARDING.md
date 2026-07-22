---
questions:
  - id: user_name
    prompt: What should your agents call you?
    type: string
    required: true
  - id: timezone
    prompt: What timezone do you live in (IANA name, e.g. Europe/Lisbon)?
    type: string
    required: true
  - id: working_hours
    prompt: When are your usual working hours?
    type: string
  - id: sacred_time
    prompt: Which blocks of time are sacred — never to be scheduled over or interrupted?
    type: list
    re_ask: true
  - id: red_lines
    prompt: What should your agents never do without asking you first?
    type: list
  - id: diff_review
    prompt: Should installs always show you a diff for approval, or auto-accept?
    type: enum
---

# The global bootstrap interview

This is the first interview a new user ever runs (BOOTSTRAP.md step 2). It writes the
**root** `MOD.md` — the global overlay every capability's transform reads. Tone: brief and
warm; the user just pasted an install command, don't make this feel like a tax form.

Script:

1. Open with what this is: "Before I wire anything up, I need a few facts about you that
   every capability will reuse — two minutes, and you can change any answer later."
2. **`user_name`**, **`timezone`** — just ask. If the system timezone is obvious, offer it
   as the default rather than asking cold.
3. **`working_hours`** — a plain phrase is fine ("9–18 weekdays, quiet Fridays"). Put the
   literal phrase in the answer; anything richer ("mornings are deep work — no meetings
   before noon") goes to the body as nuance.
4. **`sacred_time`** — explain why it's asked: scheduled agents will avoid these windows.
   Family dinners, gym, religious observance, school pickup — whatever they name, keep
   their words. `re_ask: true` because lives change; confirm on every re-run.
5. **`red_lines`** — frame concretely: "things an agent must never do unattended — send
   messages as you? spend money? touch the calendar? contact specific people?" These are
   behavioral constraints every capability inherits.
6. **`diff_review`** — options are exactly `always-review` or `auto-accept`. Recommend
   `always-review`; note that `auto-accept` is their right (§5.4) and is recorded here as
   the standing answer the diff gate reads.
7. Close by reading back a one-paragraph summary, then draft MOD.md and show it.

Everything the user says beyond the typed answers is nuance — capture it in the body under
`## Preferences`, `## Sacred time`, `## Red lines` headings, in their own phrasing.
