# capability-lifecycle

The whole life of a capability, shipped as one capability: install, upgrade, remove,
onboard, import, build, contribute, evolve. After bootstrap, "install gtd-capture" triggers
a real skill in your harness; nothing depends on re-reading repo files.

Everything lives in the household (`~/aos`): `upstream/` the pristine kit clone,
`personal/` your private repo — your `MOD.md` files, the pinned renders your harness
symlinks to, your private capabilities — and `vendor/` for third-party skills this
capability references rather than copies. The `capability-evolve` skill writes your MOD,
`capability-upgrade` re-applies it on every upgrade (review = a git diff in your own repo).
Bookkeeping — manifest parsing, the lockfile, every sha256 and link, and every skill's
installed name — belongs to the bundled [`aos-lock` tool](tool/): judgment stays with the
agent, names and hashes never do.

| Piece | What it is |
|---|---|
| `skills/capability-lifecycle/` | entry skill: the map, the Experience rules, `reference/` (contract, naming, overlay, no-cheatsheet) |
| `skills/install/` | install a capability: manifest → deps → name gate → interview → render into `personal/` → STAGE→GATE→EXECUTE → symlink + record |
| `skills/upgrade/` | pull upstream, fold drift into MOD.md, re-render upstream × MOD.md, git-diff gate, retire absorbed statements |
| `skills/remove/` | lockfile-driven exact removal; MOD.md always survives |
| `skills/onboard/` | the interview engine (§3.2): a capability's `ONBOARDING.md` → the user's `MOD.md`. Also owns the global bootstrap interview — identity, timezone, sacred time, red lines → the root `MOD.md` |
| `skills/import/` | wrap → share (§6): inventory the harness, cluster, map to package primitives, split mechanism from nuance, emit `capabilities/<id>-draft/` + `GAP.md`. Read-only on the live setup |
| `skills/build/` | the MARS building-mode detector (§9) plus intake → research → design → approval → build. Nothing durable gets written without an approved design |
| `skills/contribute/` | change a capability's shipped source, for everyone — and draft the upstream contribution when the user confirms |
| `skills/evolve/` | change how an installed capability behaves *for you*, recorded so it survives upgrades; promotes upstream when generally useful (signal-gated, offer-only) |
| `skills/capability-lifecycle/reference/harness-<runtime>.md` | the per-harness cheat-sheets (hermes · nanoclaw v1+v2 · openclaw · nanobot) — reference files of the skill that reads them, so they travel with the render |
| `tool/` | `aos-lock` — deterministic manifest, installed-name, and lockfile verbs |

Installed skill names are computed, not authored: the ids above are capability-local, and
`skill_prefix: capability-` makes them `capability-install`, `capability-onboard`,
`capability-build`, and so on. One flat skill namespace per harness means a name is
single-owner, so `aos-lock skills --check` gates every install against the household, the
lockfile, and the skills your harness already has. See
`skills/capability-lifecycle/reference/naming.md`.

For generic skill craft — drafting, description-trigger tuning, eval loops — this
capability points at Anthropic's [`skill-creator`](https://github.com/anthropics/skills)
and keeps it current under `vendor/`. It is never copied into this repo; the aos-specific
rules (identity, uniqueness, `used_by` scoping, `{{mod}}` slots) stay in
`reference/naming.md`.

Spec one-pager: [capability-lifecycle.md](https://github.com/AlmogBaku/aos/blob/spec/capabilities/capability-lifecycle.md)

| Harness | Status |
|---|---|
| Hermes | ✅ e2e-tested for real |
| NanoClaw (v1+v2), OpenClaw, Nanobot | 🧪 cheat-sheet shipped, research-drafted |
| Claude Code | 🧪 cheat-sheet shipped, research-drafted — no runner yet |
| OpenCode | 📋 no sheet yet — the no-cheat-sheet path applies |
