---
questions:
  - id: open_command
    prompt: >-
      Command template that opens one new titled session, runs exactly one turn from the prompt
      file, prints the first reply on stdout and a `session_id: <id>` line, and exits 0 on
      success. Placeholders: {profile} {skills} {workdir} {title} {prompt_file}.
    type: string
    required: true
---

# open-session onboarding

Derive the answer from this skill's `reference/<runtime>.md` for the harness being installed into
(no such file: derive from the harness CLI and flag it unverified at the diff gate) — never ask the
user. `{profile}` is the literal `default` for a harness's root profile. Use absolute paths.
