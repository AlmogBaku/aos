# onboarding

The interview engine (ARCHITECTURE §3.2). Reads a capability's `ONBOARDING.md` — typed
questions in frontmatter, conversational script in the body — interviews the user, and
writes their `MOD.md` overlay: typed answers in frontmatter, prose nuance in the body,
secrets as `{store, key}` references with values in the harness store.

Also owns the **global bootstrap interview** (its own `ONBOARDING.md`): identity, timezone,
working hours, sacred time, red lines → the root `MOD.md`. First thing a new user runs
(`docs/BOOTSTRAP.md` step 2).

Re-runs ask only missing or `re_ask` questions; `--refresh` re-asks everything and shows a
diff before writing. Nothing self-deletes.

Spec one-pager: [onboarding.md](https://github.com/AlmogBaku/aos/blob/spec/capabilities/onboarding.md)

## Support matrix

| Harness | Status | Runner |
|---|---|---|
| Hermes | hook | @AlmogBaku |
| NanoClaw | unsupported (no runner yet) | — |
| OpenClaw | unsupported (no runner yet) | — |
