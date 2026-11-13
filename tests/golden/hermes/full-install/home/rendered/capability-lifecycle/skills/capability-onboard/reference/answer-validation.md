# Answer validation

Deterministic; run before writing MOD.md. A failing answer goes back to the user — never
silently coerce.

| type | valid when |
|---|---|
| `string` | non-empty after trimming |
| `number` | parses as a number; keep numeric form in YAML |
| `boolean` | clear yes/no — store `true`/`false` |
| `enum` | exactly one of the script's options, verbatim |
| `list` | YAML list of strings; empty only if not `required` |
| `path` | absolute or `~/`-prefixed; warn (don't block) if it doesn't exist |

- Every `required: true` question has an answer, or the interview is reported incomplete
  — never fake a value.
- Answer keys = question `id`s exactly; no invented keys.
- `secret: true` answers appear only under `secrets:` as `{store, key}` — never under
  `answers:`.
- Timezones: IANA names (`Europe/Lisbon`), not offsets. Clock times: 24h `HH:MM`.
