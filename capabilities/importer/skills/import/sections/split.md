# Stage 4 — Split generic from personal

The inverse install transform, sentence by sentence: for every instruction, name, value
in the mapped artifacts, ask *"would a stranger installing this want exactly this?"*

- **Mechanism** (stays in the skeleton): the flow, the formats, the schedule *existence*,
  the safety rules, the zone structure.
- **Nuance** (goes to draft MOD.md): names, goals, injury lists, phrasing preferences,
  specific hours, channel ids, thresholds tuned to this user. Where a nuance filled a
  structural slot, leave a `{{mod: <slot>}}` marker in the skeleton.
- **Questions** (go to `ONBOARDING.md`): every nuance you extracted implies a question
  the next user must be asked. Draft the question list (typed frontmatter) + a minimal
  script — the interview is how the capability re-personalizes.
- Personal data that is neither mechanism nor a needed answer (history, logs, old
  entries): **neither** — leave it on the harness, note in GAP that it wasn't imported.

When genuinely unsure, nuance-side + a GAP note (see the skill's ground rules).
