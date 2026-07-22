# Answer validation

Deterministic checks — run them mechanically before writing MOD.md ([D] step, §3.2).
An answer that fails validation goes back to the user; never silently coerce.

Per `type`:

| type | valid when |
|---|---|
| `string` | non-empty string after trimming |
| `number` | parses as a number (int or float); keep the numeric form in YAML |
| `boolean` | a clear yes/no — store `true`/`false`, never "yeah" |
| `enum` | exactly one of the options the question's script offers, verbatim |
| `list` | YAML list of strings; empty list only if the question is not `required` |
| `path` | absolute or `~/`-prefixed path; warn (don't block) if it doesn't exist yet |

Cross-cutting:

- Every `required: true` question has an answer (unless the user explicitly deferred —
  then the interview is incomplete: say so, don't fake a value).
- Answer keys in MOD.md frontmatter are exactly the question `id`s — no invented keys
  (the tier-1 linter enforces the same rule on fixtures: the questions *are* the schema).
- `secret: true` answers never appear under `answers:` — only under `secrets:` as
  `{store, key}` references.
- Timezone answers: must be an IANA zone name (`Europe/Lisbon`), not an offset.
- Cron-hour answers: 24h `HH:MM`.
