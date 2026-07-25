# Stage 5 — Emit

Write under the user's personal root (`<home>/personal`):

- `capabilities/<id>-draft/` — full §2.1 skeleton: `CAPABILITY.md`, `README.md` (support
  matrix: this harness only, this user as runner), `skills/`, `agents/`, `ONBOARDING.md`,
  `MOD.example.md` (invented placeholder answers, zero personal data), `kb/` templates.
- `capabilities/<id>-draft/MOD.md` — the user's actual nuances (overlay family: never in
  a PR).
- `capabilities/<id>-draft/GAP.md` — per the GAP format in `reference/gap-report.md`
  (the skill's checklist links it).

Then:
1. Run the repo's tier-1 lint over the draft if `tools/` exists.
2. Print the punch list: GAP items, lint findings, the `<id>-draft` → `<id>` rename.
3. State what a PR must not contain: their MOD.md, any secret, any personal KB content.

Never open the PR yourself — the contribution flow (the
`capability-contribute` skill, contribute reference) drafts and offers; every
upstream write waits for the user's explicit yes. Until then the draft lives
happily in `personal/`.
