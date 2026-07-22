# Stage 5 — Emit

Write, under the user's clone:

- `capabilities/<id>-draft/` — the full §2.1 skeleton: `CAPABILITY.md` (typed
  frontmatter + install narrative), `README.md` (support matrix listing *only this
  harness*, this user as runner), `skills/`, `agents/`, `ONBOARDING.md`, `MOD.example.md`
  (placeholder answers — **not** the user's), `kb/` templates as mapped.
- `capabilities/<id>-draft/MOD.md` — the draft overlay holding the user's actual nuances
  (overlay family: stays theirs, never in a PR).
- `capabilities/<id>-draft/GAP.md` — see [gap-report.md](gap-report.md).

Then: run the repo's tier-1 lint over the draft if `tools/` exists (the `-draft` suffix
relaxes nothing — a draft that lints is an hour from a PR); print the author's punch
list (GAP items + lint findings + the rename from `<id>-draft` to `<id>`); and remind
them what a PR must not contain (their MOD.md, any secret, any personal KB content).

You never open the PR. The author reviews, genericizes further if needed, and submits.
