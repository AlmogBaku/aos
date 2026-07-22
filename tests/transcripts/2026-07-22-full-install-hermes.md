Installed `kb`, `onboarding`, and `gtd-capture` in order.

Verification:
- `node tools/golden/check.mjs --live` → `golden: 0 failures`
- Lockfile hashes verified: 88 artifacts
- Root Hermes config, root skills, and root cron jobs unchanged
- No writes remain outside the allowed profile/sandbox scopes
- Schedules are single-owner and correctly namespaced

Profiles:
- `~/.hermes/profiles/aos-test`
- `~/.hermes/profiles/aos-archiver`
- `~/.hermes/profiles/aos-drainer`

Schedules:
- `aos:kb:nightly-promote` → archiver, `30 23 * * *`, job `3ffac5368e3b`
- `aos:kb:weekly-lint` → archiver, `0 7 * * 6`, job `ad82c95bc9e2`
- `aos:kb:kb-sync` → archiver, every 5 minutes, job `f798c341a721`
- `aos:gtd-capture:nightly-drain` → drainer, `47 23 * * *`, job `0d0bef62b24a`

Degraded mode:
- Outbound messaging is unavailable in the namespaced profiles, so reminders use local schedule delivery/reporting rather than WhatsApp delivery.

KBs initialized:
- `/home/anakin/aos/tests/.sandbox/kb/personal-kb`
- `/home/anakin/aos/tests/.sandbox/kb/acme-kb`
- Both have methodology scaffolding, grants, inboxes, git bootstrap commits, and drainer grants.

Lockfile:
- `/home/anakin/aos/tests/.sandbox/aos-clone/.aos/installs.lock.yaml`

Files written/materialized:

`aos-test`:
- `~/.hermes/profiles/aos-test/SOUL.md`
- `~/.hermes/profiles/aos-test/config.yaml`
- `~/.hermes/profiles/aos-test/skills/onboarding-interview/SKILL.md`
- `~/.hermes/profiles/aos-test/skills/onboarding-interview/sections/answer-validation.md`
- `~/.hermes/profiles/aos-test/skills/kb-route/SKILL.md`
- `~/.hermes/profiles/aos-test/skills/kb-authz-check/SKILL.md`
- `~/.hermes/profiles/aos-test/skills/kb-init/SKILL.md`
- `~/.hermes/profiles/aos-test/skills/kb-adopt/SKILL.md`
- `~/.hermes/profiles/aos-test/skills/gtd-capture-capture/SKILL.md`
- `~/.hermes/profiles/aos-test/skills/gtd-capture-capture/sections/entry-format.md`
- `~/.hermes/profiles/aos-test/skills/gtd-capture-format-entry/SKILL.md`

`aos-archiver`:
- `~/.hermes/profiles/aos-archiver/SOUL.md`
- `~/.hermes/profiles/aos-archiver/config.yaml`
- `~/.hermes/profiles/aos-archiver/cron/jobs.json`
- `~/.hermes/profiles/aos-archiver/scripts/kb-sync.sh`
- `~/.hermes/profiles/aos-archiver/scripts/kb-sync-all.sh`
- `~/.hermes/profiles/aos-archiver/skills/kb-authz-check/SKILL.md`
- `~/.hermes/profiles/aos-archiver/skills/kb-lint/SKILL.md`

`aos-drainer`:
- `~/.hermes/profiles/aos-drainer/SOUL.md`
- `~/.hermes/profiles/aos-drainer/config.yaml`
- `~/.hermes/profiles/aos-drainer/cron/jobs.json`
- `~/.hermes/profiles/aos-drainer/skills/gtd-capture-drain/SKILL.md`
- `~/.hermes/profiles/aos-drainer/skills/gtd-capture-drain/drain-prompt.md`
- `~/.hermes/profiles/aos-drainer/skills/gtd-capture-format-entry/SKILL.md`

KB files, each under both `personal-kb/` and `acme-kb/`:
- `.gitattributes`
- `.gitignore`
- `AGENTS.md`
- `SCHEMA.md`
- `index.md`
- `log.md`
- `_ops/AGENTS.md`
- `entities/AGENTS.md`
- `entities/communities/.gitkeep`
- `entities/companies/.gitkeep`
- `entities/people/.gitkeep`
- `entities/products/.gitkeep`
- `raw/AGENTS.md`
- `raw/calendar/.gitkeep`
- `raw/captures/.gitkeep`
- `raw/clippings/.gitkeep`
- `raw/emails/.gitkeep`
- `raw/meetings/.gitkeep`
- `state/AGENTS.md`
- `ops/AGENTS.md`
- `ops/inbox.md`
- `ops/tasks/.gitkeep`
- `ops/reviews/closeouts/.gitkeep`
- `ops/reviews/monthly/.gitkeep`
- `ops/reviews/weekly/.gitkeep`
- `projects/.gitkeep`
- `queries/.gitkeep`
- `comparisons/.gitkeep`
- `concepts/.gitkeep`
- `domains/.gitkeep`
- `drafts/.gitkeep`
- `_archive/captures/.gitkeep`

The lockfile contains SHA-256 records for all 88 install artifacts.
