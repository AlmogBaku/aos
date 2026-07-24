# capability-lifecycle

Install, upgrade, remove, and evolve — the capability lifecycle itself, shipped as a
capability. After bootstrap, "install gtd-capture" triggers a real skill in your harness;
nothing depends on re-reading repo files. Everything lives in the household (`~/aos`):
`upstream/` the pristine kit clone, `personal/` your private repo — your `MOD.md`
ledgers, the pinned renders your harness symlinks to, your private capabilities. The
`capability-evolver` skill writes the ledger, the `capability-upgrader` re-applies it on
every upgrade (review = a git diff in your own repo). Bookkeeping (manifest parsing, the
lockfile, every sha256 and link) belongs to the bundled [`aos-lock` tool](tool/) —
judgment stays with the agent, hashes never do.

| Piece | What it is |
|---|---|
| `skills/capability-lifecycle/` | entry skill: the map, the Experience rules, `reference/` (contract, overlay, no-cheatsheet) |
| `skills/capability-installer/` | install a capability: manifest → deps → interview → render into `personal/` → STAGE→GATE→EXECUTE → symlink + record |
| `skills/capability-upgrader/` | the aos upgrader: pull upstream, fold drift into the ledger, re-render upstream × MOD.md, git-diff gate, retire absorbed lines |
| `skills/capability-remover/` | lockfile-driven exact removal; MOD.md always survives |
| `skills/capability-evolver/` | change how an installed capability behaves — recorded so it survives upgrades; promotes it upstream when it's generally useful (signal-gated, offer-only) |
| `harnesses/<runtime>.md` | the per-harness cheat-sheets (hermes · nanoclaw v1+v2 · openclaw · nanobot) |
| `tool/` | `aos-lock` — deterministic manifest + lockfile verbs |

| Harness | Status |
|---|---|
| Hermes | ✅ e2e-tested for real |
| NanoClaw (v1+v2), OpenClaw, Nanobot | 🧪 cheat-sheet shipped, research-drafted |
| Claude Code, OpenCode | 📋 no sheet yet — the no-cheat-sheet path applies |
