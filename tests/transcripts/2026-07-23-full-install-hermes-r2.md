Installed `kb`, `onboarding`, and `gtd-capture` in the required order.

Verification passed:
- `node tools/golden/check.mjs --live` → `golden: 0 failures`
- `bash tools/check.sh` → 4 capabilities, 0 errors, 0 warnings
- Lockfile SHA-256 verification → 92/92 artifacts valid
- Cron ownership and namespacing verified
- Root Hermes config and root cron hashes unchanged
- Disposable bundled skills removed from the `aos-*` profiles
- Profile wrapper files created by `hermes profile create` moved to trash after profile creation

Profiles:
- `/home/anakin/.hermes/profiles/aos-test`
- `/home/anakin/.hermes/profiles/aos-archiver`
- `/home/anakin/.hermes/profiles/aos-drainer`

Schedules:
- `aos:kb:nightly-promote` — archiver — `30 23 * * *` — `38d16587b35a`
- `aos:kb:weekly-lint` — archiver — `0 7 * * 6` — `a257caa83871`
- `aos:kb:kb-sync` — archiver — every 5 minutes — `9b178121dde5`
- `aos:gtd-capture:nightly-drain` — drainer — `47 23 * * *` — `95682ee5f07f`

Degraded mode:
- Outbound messaging is unavailable in the namespaced profiles. Reminders use local schedule delivery/reporting instead of WhatsApp delivery.

Lockfile:
- `/home/anakin/aos/tests/.sandbox/aos-clone/.aos/installs.lock.yaml`

Every materialized artifact and its SHA-256 is recorded there. Files written:

`aos-test`
- `/home/anakin/.hermes/profiles/aos-test/SOUL.md`
- `/home/anakin/.hermes/profiles/aos-test/config.yaml`
- `skills/onboarding-interview/SKILL.md`
- `skills/onboarding-interview/sections/answer-validation.md`
- `skills/kb-route/SKILL.md`
- `skills/kb-authz-check/SKILL.md`
- `skills/kb-init/SKILL.md`
- `skills/kb-adopt/SKILL.md`
- `skills/gtd-capture-capture/SKILL.md`
- `skills/gtd-capture-capture/sections/entry-format.md`
- `skills/gtd-capture-format-entry/SKILL.md`

`aos-archiver`
- `/home/anakin/.hermes/profiles/aos-archiver/SOUL.md`
- `/home/anakin/.hermes/profiles/aos-archiver/config.yaml`
- `/home/anakin/.hermes/profiles/aos-archiver/cron/jobs.json`
- `/home/anakin/.hermes/profiles/aos-archiver/scripts/kb-sync.sh`
- `/home/anakin/.hermes/profiles/aos-archiver/scripts/kb-sync-all.sh`
- `skills/kb-authz-check/SKILL.md`
- `skills/kb-lint/SKILL.md`

`aos-drainer`
- `/home/anakin/.hermes/profiles/aos-drainer/SOUL.md`
- `/home/anakin/.hermes/profiles/aos-drainer/config.yaml`
- `/home/anakin/.hermes/profiles/aos-drainer/cron/jobs.json`
- `skills/gtd-capture-drain/SKILL.md`
- `skills/gtd-capture-drain/drain-prompt.md`
- `skills/gtd-capture-format-entry/SKILL.md`

KBs:
- `/home/anakin/aos/tests/.sandbox/kb/personal-kb`
- `/home/anakin/aos/tests/.sandbox/kb/acme-kb`

Each KB contains the same 34 initialized files:
- `.gitattributes`, `.gitignore`, `AGENTS.md`, `SCHEMA.md`, `index.md`, `log.md`
- `_archive/captures/.gitkeep`
- `_ops/.gitkeep`, `_ops/AGENTS.md`
- `comparisons/.gitkeep`, `concepts/.gitkeep`, `domains/.gitkeep`, `drafts/.gitkeep`
- `entities/AGENTS.md`
- `entities/communities/.gitkeep`
- `entities/companies/.gitkeep`
- `entities/people/.gitkeep`
- `entities/products/.gitkeep`
- `ops/AGENTS.md`, `ops/inbox.md`
- `ops/reviews/closeouts/.gitkeep`
- `ops/reviews/monthly/.gitkeep`
- `ops/reviews/weekly/.gitkeep`
- `ops/tasks/.gitkeep`
- `projects/.gitkeep`, `queries/.gitkeep`
- `raw/AGENTS.md`
- `raw/calendar/.gitkeep`
- `raw/captures/.gitkeep`
- `raw/clippings/.gitkeep`
- `raw/emails/.gitkeep`
- `raw/meetings/.gitkeep`
- `state/.gitkeep`, `state/AGENTS.md`
