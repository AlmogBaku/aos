# Contributing

The fastest way to move anything here is to build against it — **a working PR outranks
an RFC comment**. This page is the mechanics; the philosophy is in the
[README](README.md#why-this-is-open-source).

## The two branches

| Branch | What lives there | How it changes |
|---|---|---|
| `main` | The built kit: capabilities, cheat-sheets, docs, tooling, tests | PRs, gated by CI |
| [`spec`](https://github.com/AlmogBaku/aos/tree/spec) | The paper: ARCHITECTURE.md, RFCs, one-pagers, design deep-dives | Firm-position discipline + RFCs (below) |

Spec docs are never copied onto `main`; artifacts on `main` link to them. When building
reveals the spec is wrong, the spec gets fixed — every such mismatch gets a row in
[docs/BUILD-GAPS.md](docs/BUILD-GAPS.md), artifact-side fixes land in the same `main`
commit, spec-side fixes land on `spec`.

## The one gate

```bash
bash tools/check.sh
```

Run it before every commit. It runs exactly what CI runs: the `base`-tool unit suite +
example-base lint (tier 0, needs [`uv`](https://docs.astral.sh/uv/)), the kit linter and
its selftest (tier 1), and the golden structural checks (tier 2). Details:
[docs/TESTING.md](docs/TESTING.md).

Two things CI enforces that bite people:

- **Version bumps.** If a PR touches a capability's files, its `CAPABILITY.md` `version`
  must bump — upgrades key off it. Check locally with
  `node tools/lint/aos-lint.mjs --base origin/main`.
- **Golden snapshots.** If your change alters what an install materializes, re-render
  the snapshots under `tests/golden/hermes/` (the diff is the review artifact) — and the
  e2e is a **real install** into a disposable Hermes profile, never a simulation
  ([tests/golden/PROTOCOL.md](tests/golden/PROTOCOL.md)).

## Contributing a capability

The shape is fixed and lint-enforced
([spec §2](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#2-the-capability-package)):

```text
capabilities/<id>/
  CAPABILITY.md           # typed frontmatter + the installer's prose briefing
  README.md               # for humans & PR review: what it does + support matrix
  skills/<id>/SKILL.md    # the ENTRY skill (named after the capability) — required
  skills/<id>/reference/  # depth, exactly one hop — no reference chains
  skills/<skill>/         # focused skills, each a valid Agent Skills folder
  agents/<name>.agent.yaml + agents/<name>/   # only if it needs its own agent
  ONBOARDING.md + MOD.example.md              # as a pair, or neither
  kb/ · adapters/<harness>/                   # only if needed
```

Start from the worked example: **gtd-capture** is walked file-by-file in
[design/capability-anatomy.md](https://github.com/AlmogBaku/aos/blob/spec/design/capability-anatomy.md),
and its manifest is the spec's own example. Or don't hand-roll at all — the kit's
**importer** capability wraps what's already in your harness: ask your agent to import
it, review the draft + `GAP.md` it emits, open the PR.

House rules the linter can't fully check:

- **Skills are scoped.** Every skill declares `used_by`; `used_by` cannot name another
  capability's agent (open RFC-009). Capabilities compose through the shared `main`
  agent or a tool on PATH — never by loading a foreign skill.
- **Shipped software is judgment-free.** A capability tool is standalone, behind a
  process boundary: files and exit codes, no LLM calls inside
  ([spec §2.4](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#24-harness-native-code-capabilities-ship-software)).
- **No program anywhere.** `install`/`update`/`remove`/`import` are conversations the
  harness agent performs. Per-harness support is a cheat-sheet, never adapter code.
- **Rule of two.** A manifest field must have two in-repo machine consumers or stay
  prose. Don't "helpfully" add fields.
- **The overlay is user-owned.** Never ship, write, or merge any `MOD.md` or
  `kb-registry.yaml` (fixtures and golden snapshots are the one exemption).

> [!WARNING]
> **This repo is public and capabilities are extracted from real setups.** Nothing
> personal lands in a committed file: no real names, employers, or relationships; no
> secrets or tokens; no actual KB content. `ONBOARDING.md` ships *questions*;
> `MOD.example.md` ships *placeholder* answers. Lift the mechanism, genericize the
> content; when in doubt, redact. The `secrets/` lint family backstops this — it does
> not replace judgment.

## Contributing a harness cheat-sheet

One document makes a harness supported: `harnesses/<name>/CHEATSHEET.md` with the six
sections of
[spec §5.2](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#52-cheat-sheets-the-adapter-is-knowledge-not-code)
(primitive mapping, materialization, introspection, secrets, removal, feature notes).
[`harnesses/hermes/CHEATSHEET.md`](harnesses/hermes/CHEATSHEET.md) is the reference.
The bar: an LLM with only your cheat-sheet + a capability + a fixture overlay must
produce a correct install.

## Changing a decision

Check [spec §8](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#8-decision-index)
first — every decision is one of two kinds:

- **Firm position** → open an issue naming the section, **with a counter-proposal**.
  Quietly rewording the spec is not a move.
- **Open RFC** (`rfcs/RFC-00N-*.md`) → comment on the RFC before its auto-accept
  deadline. RFCs are never resolved inside ARCHITECTURE or a capability page; builds
  proceed but defer the contested behavior to the RFC.

## PR checklist

- [ ] `bash tools/check.sh` is green
- [ ] Capability files changed → `version` bumped
- [ ] Install output changed → goldens re-rendered (real run, not simulated)
- [ ] Spec mismatch discovered → `docs/BUILD-GAPS.md` row (+ spec-branch fix if spec-side)
- [ ] Nothing personal, no secrets, no real KB content
- [ ] New docs/diagrams: relative links resolve; mermaid parses

## License

MIT — by contributing you agree your work ships under it.
