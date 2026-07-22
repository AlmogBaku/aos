# Dana Fixture — the test persona

Every fixture in this tree uses one invented persona, so no test ever needs personal data.
If a fixture needs a value not listed here, add it here first — never improvise real-looking
data elsewhere.

| Fact | Value |
|---|---|
| Name | Dana |
| Timezone | Europe/Lisbon |
| Employer | Acme Corp (the shared-KB tenant) |
| Messaging | `whatsapp:+000000000000` |
| Email | `dana@example.com` |
| KBs | `personal-kb` (private, default) · `acme-kb` (shared) |
| Drain hour | 23:47 (deliberately odd — greppable) |

## Sentinels

Fixture nuances carry globally unique **sentinel strings**. A structural check greps for a
sentinel in the artifact the render should have carried it into — deterministic proof that a
MOD.md nuance survived the agentic transform.

| Sentinel | Lives in | Must surface in |
|---|---|---|
| `single 🦜 emoji` | gtd-capture MOD (capture confirm preference) | rendered capture skill |
| `choir practice Thursdays 19:00-21:00` | global MOD sacred_time | any schedule-touching render |
| `23:47` | gtd-capture MOD drain hour | drainer cron job schedule |
| `violet-heron` | gtd-capture user-b MOD | user-b render only (divergence proof) |
| `FAKE-SECRET-VALUE-1` | fixture secret value | harness secret store only — never MOD.md, never skills |
