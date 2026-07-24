# capability-lifecycle

Install, upgrade, remove, and evolve — the capability lifecycle itself, shipped as a
capability. After bootstrap, "install gtd-capture" triggers a real skill in your harness;
nothing depends on re-reading repo files. `MOD.md` is your ledger of personalization: the
`capability-evolver` skill writes it, the `capability-upgrader` re-applies it on every
upgrade. Bookkeeping (manifest parsing, the lockfile, every sha256) belongs to the
bundled [`aos-lock` tool](tool/) — judgment stays with the agent, hashes never do.

| Piece | What it is |
|---|---|
| `skills/capability-lifecycle/` | entry skill: the map, the Experience rules, `reference/` (contract, overlay, no-cheatsheet) |
| `skills/capability-installer/` | install a capability: manifest → deps → interview → transform → STAGE→GATE→EXECUTE → record |
| `skills/capability-upgrader/` | the aos upgrader: git pull, fold drift into the ledger, re-render upstream × MOD.md |
| `skills/capability-remover/` | lockfile-driven exact removal; MOD.md always survives |
| `skills/capability-evolver/` | change how an installed capability behaves — and record it so it survives upgrades |
| `harnesses/<runtime>.md` | the per-harness cheat-sheets (hermes · nanoclaw v1+v2 · openclaw · nanobot) |
| `tool/` | `aos-lock` — deterministic manifest + lockfile verbs |

| Harness | Status |
|---|---|
| Hermes | ✅ e2e-tested for real |
| NanoClaw (v1+v2), OpenClaw, Nanobot | 🧪 cheat-sheet shipped, research-drafted |
| Claude Code, OpenCode | 📋 no sheet yet — the no-cheat-sheet path applies |
