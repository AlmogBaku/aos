Removed all three capabilities from the `aos-*` namespace.

Removed cron jobs via Hermes CLI:
- `aos:kb:nightly-promote` — `3ffac5368e3b`
- `aos:kb:weekly-lint` — `ad82c95bc9e2`
- `aos:kb:kb-sync` — `f798c341a721`
- `aos:gtd-capture:nightly-drain` — `0d0bef62b24a`

No matching `cron/output/<id>*` artifacts existed.

Removed materialized skill directories:
- `~/.hermes/profiles/aos-archiver/skills/kb-authz-check/`
- `~/.hermes/profiles/aos-archiver/skills/kb-lint/`
- `~/.hermes/profiles/aos-drainer/skills/gtd-capture-drain/`
- `~/.hermes/profiles/aos-drainer/skills/gtd-capture-format-entry/`
- `~/.hermes/profiles/aos-test/skills/gtd-capture-capture/`
- `~/.hermes/profiles/aos-test/skills/gtd-capture-format-entry/`
- `~/.hermes/profiles/aos-test/skills/kb-adopt/`
- `~/.hermes/profiles/aos-test/skills/kb-authz-check/`
- `~/.hermes/profiles/aos-test/skills/kb-init/`
- `~/.hermes/profiles/aos-test/skills/kb-route/`
- `~/.hermes/profiles/aos-test/skills/onboarding-interview/`

Removed recorded scripts:
- `~/.hermes/profiles/aos-archiver/scripts/kb-sync-all.sh`
- `~/.hermes/profiles/aos-archiver/scripts/kb-sync.sh`

Removed all capability marker blocks from:
- `~/.hermes/profiles/aos-test/SOUL.md`
- `~/.hermes/profiles/aos-archiver/SOUL.md`
- `~/.hermes/profiles/aos-drainer/SOUL.md`

Unset recorded `model.default` keys from all three profiles.

Updated:
- `~/aos/tests/.sandbox/aos-clone/.aos/installs.lock.yaml`

The lockfile now has empty `created_profiles`, `config_keys`, `capabilities`, and `artifacts` fields. The three profiles remain intact.

Preserved as required:
- `CLONE/MOD.md`
- `CLONE/kb-registry.yaml`
- Capability overlay files
- Scaffolded user KBs under `~/aos/tests/.sandbox/kb`

KBs are user data and are never deleted by capability removal.

Verified: no aos cron jobs, origins, marker blocks, recorded skills, or scripts remain.
