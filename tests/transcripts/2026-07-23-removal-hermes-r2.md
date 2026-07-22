Removed all three capabilities from the `aos-*` profile namespace.

Cron jobs removed via Hermes CLI:
- `aos:kb:nightly-promote` — `38d16587b35a`
- `aos:kb:weekly-lint` — `a257caa83871`
- `aos:kb:kb-sync` — `9b178121dde5`
- `aos:gtd-capture:nightly-drain` — `95682ee5f07f`

Cron output artifacts:
- No `<id>*` artifacts existed.
- Removed the empty `cron/output/` directories recreated by Hermes.

Materialized skill directories removed:
- `/home/anakin/.hermes/profiles/aos-archiver/skills/kb-authz-check/`
- `/home/anakin/.hermes/profiles/aos-archiver/skills/kb-lint/`
- `/home/anakin/.hermes/profiles/aos-drainer/skills/gtd-capture-drain/`
- `/home/anakin/.hermes/profiles/aos-drainer/skills/gtd-capture-format-entry/`
- `/home/anakin/.hermes/profiles/aos-test/skills/gtd-capture-capture/`
- `/home/anakin/.hermes/profiles/aos-test/skills/gtd-capture-format-entry/`
- `/home/anakin/.hermes/profiles/aos-test/skills/kb-adopt/`
- `/home/anakin/.hermes/profiles/aos-test/skills/kb-authz-check/`
- `/home/anakin/.hermes/profiles/aos-test/skills/kb-init/`
- `/home/anakin/.hermes/profiles/aos-test/skills/kb-route/`
- `/home/anakin/.hermes/profiles/aos-test/skills/onboarding-interview/`

Recorded scripts removed:
- `/home/anakin/.hermes/profiles/aos-archiver/scripts/kb-sync-all.sh`
- `/home/anakin/.hermes/profiles/aos-archiver/scripts/kb-sync.sh`

Config keys unset via Hermes CLI:
- `model.default` from `aos-test`
- `model.default` from `aos-archiver`
- `model.default` from `aos-drainer`

Marker blocks removed from:
- `/home/anakin/.hermes/profiles/aos-test/SOUL.md`
- `/home/anakin/.hermes/profiles/aos-archiver/SOUL.md`
- `/home/anakin/.hermes/profiles/aos-drainer/SOUL.md`

Updated:
- `/home/anakin/aos/tests/.sandbox/aos-clone/.aos/installs.lock.yaml`

The lockfile now has empty `created_profiles`, `config_keys`, `capabilities`, and `artifacts`.

Preserved:
- All three profiles
- `CLONE/MOD.md`
- `CLONE/kb-registry.yaml`
- Capability overlay files
- User KBs under `/home/anakin/aos/tests/.sandbox/kb`

Verification:
- All three profiles still exist.
- No scheduled jobs remain.
- No recorded capability skills, scripts, markers, origins, or cron output directories remain.
- User KB directories and clone overlay files still exist.
