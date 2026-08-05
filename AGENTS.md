# AGENTS.md

For any coding agent working in this repo. `CLAUDE.md` is a symlink to this file — edit this
one, never replace the symlink with a copy.

## Read first

1. **`bash tools/check.sh` before every commit.** The one gate; runs exactly what CI runs.
2. **Never commit to `main` or `spec`** — branch-protected, maintainers included. Branch, then PR.
3. **Sign every commit** (`git commit -s`). Retrofitting DCO rewrites every SHA, and `docs/BUILD-GAPS.md` cites SHAs.
4. **Never push, fork, open a PR or file an issue without the user's explicit approval.**

Full rules: [CONTRIBUTING.md](CONTRIBUTING.md).

## What this repo is

`main` is the built kit. **The spec lives only on the `spec` branch** — read it with
`git show spec:<path>`, never copy it onto main. For an unbuilt capability, its spec docs are
the only source of truth. (`aos` is a placeholder; RFC-001 picks the real name.)

A protocol plus implementations, no runtime: *capabilities* that install into an existing
harness, personalize via an interview, and survive upgrades.

| Capability | Type | Ships |
|---|---|---|
| `kb` | infra | knowledge infrastructure + the `kb` tool |
| `work-tracker` | usecase | commitments, built on kb |
| `capability-lifecycle` | infra | ten lifecycle skills + the `aos-cap` tool |

Hermes is e2e-verified. NanoClaw, OpenClaw, Nanobot, Claude Code have research-drafted
cheat-sheets.

## Commands

`uv` is the only prerequisite — no `package.json`, no `node_modules`. Lint commands elide the
prefix `uv run --quiet --project tools/aos_lint python -m`.

| | Command |
|---|---|
| everything CI runs | `bash tools/check.sh` |
| tier 0 — tool suites | `uv run tests/tool/test_kb.py` · `uv run tests/tool/test_cap.py` |
| tier 1 — lint | `aos_lint.cli` · `aos_lint.selftest` |
| tier 1 — gates | `aos_lint.gates.{retired,coverage,kb_commands,privacy}` |
| tier 2 — goldens | `aos_lint.golden.check` |
| **version-bump check** | `aos_lint.cli --base origin/main` |
| the `kb` tool ad hoc | `uv run --project capabilities/kb/tool kb --help` — 24 verbs: `init adopt migrate capture ingest pending inbox find set prune archive search links state grants lint index sync commit history refuse verify config import` |
| live e2e | `tests/golden/PROTOCOL.md`, then `aos_lint.golden.{check --live full-install,normalize}` |

- `aos_lint.cli --base origin/main` is the **only** thing that catches a missing version bump.
- `aos_lint.gates.template_drift` is outside `check.sh`: needs network, skips offline.
- **`uv tool install --force` reuses the cached wheel** — a new module silently does not ship.
  `uv cache clean <pkg>` first. Same reason to prefer `uv run --project` over `uvx --from`.
- **`BaseToolTest` is a concrete leaf (~65 tests), not a base class.** Copy its setUp.
- A capability version bump is up to **four** sites: `CAPABILITY.md`, `MOD.example.md`'s
  `onboarded_version`, and if it ships a tool, `tool/pyproject.toml` + the tool's `VERSION`.

## Layout

**On `spec`:** `ARCHITECTURE.md` is the only normative document — §2 package format, **§3 the
overlay contract (inviolable)**, §4 KB, §5 install, §7 build order, **§8 decision index**. Plus
`rfcs/`, `capabilities/*.md` one-pagers, `design/` (`capability-anatomy.md` is the worked example).

**On main:**

| Path | What |
|---|---|
| `capabilities/<id>/` | built capabilities (§2.1); each has an entry skill named after itself, depth in a sibling `reference/` one level deep |
| `.../reference/harness-<runtime>.md` | per-harness cheat-sheets — reference files of the entry skill, so they travel with the render |
| `BOOTSTRAP.md` | the agent-facing install sequence; both entry paths clone first |
| `docs/` | `CONCEPTS` (model) · `INSTALL`/`USAGE` (human) · `TESTING` · **`BUILD-GAPS`** (spec-gap ledger) · `DOGFOOD` |
| `tools/aos_lint/` | the whole repo-side toolchain: `checks/`, `gates/`, test-only `golden/` |
| `tests/` | tier-0 suites, fixtures, golden **data**, transcripts |

`aos_lint` **imports** name computation and manifest vocabulary from the shipped `aos-cap`
rather than mirroring it. `constants.py` owns `KIT_NAME`, so the RFC-001 rename is one file.

**Stay inside your own namespace.** In whatever harness you install into, you own only what you
created: `aos-*` profiles/agents, `aos:<capability>:<schedule-id>` crons, and the skill and
agent links `aos-cap skills`/`agents` names. The rest of that harness's root — `~/.hermes`,
`~/.claude`, `~/.openclaw`, the checkout root, per its cheat-sheet — is somebody's live setup.
A KB is written only under `tests/.sandbox/`; a real KB, anyone's at any path, never.
`tests/golden/prestate.sh` proves it for Hermes; a second harness needs its own.

## Rules that are easy to break

- **The overlay family** (`MOD.md`, `kb-registry.yaml`) is user-owned. Upstream never ships,
  writes or merges those paths; do not create them here. `.aos/` is machine-local, gitignored.
- **Rule of two** — a manifest field exists only once two in-repo capabilities need it
  machine-read. §2.2 lists what was deliberately left out; don't helpfully add it.
- **Extra fields: the word is `metadata`.** In an *external* schema (`SKILL.md`) our extensions
  nest under its hatch — `metadata.aos.*`. In *our own* (`CAPABILITY.md`, `.kb/base.yml`), `x-*`
  is reserved for third parties; what *we* need becomes a real field or stays prose.
- **No program anywhere** — `install`/`update`/`import` are conversational actions. Per-harness
  support is a cheat-sheet, never adapter code, and an aid rather than a gate.
- **Names are computed and single-owner (§2.5).** A skill installs as `<skill_prefix><id>`
  (`aos-cap skills`); an agent the same way (`aos-cap agents`, own namespace, same exit 17, no
  `agent_prefix` — rule of two). Skills are verbs, agents are roles. Never rename at install to
  dodge a collision; fix the package.
- **References are slots, never computed names.** Write `{{skill: <id>}}` / `{{agent: <id>}}`
  and the render substitutes. A hardcoded name rots on a prefix change; a bare id names nothing.
  A dangling slot fails the render (exit 18) and CI. A leading backslash escapes an example —
  which is what lets the docs teaching this rule survive being rendered by it.
- **Skill scoping** — every skill declares `used_by`. No cross-capability skill sharing (open
  RFC-009); capabilities compose through the shared `main` agent or a tool on PATH.
- **Entry-skill anatomy (§2.5)** — `skills/<id>/SKILL.md`, depth one level deep, no chains.
  `CAPABILITY.md` is the installer's briefing (never loaded at runtime); the entry skill is the
  runtime face.
- **KB safety** — `audience: shared` KBs never accept LLM-routed writes. Capture latency is
  sacred: routing is never a synchronous prompt.
- **Single-owner schedules** — each `schedules[]` entry runs in exactly one harness at a time.

## Changing a decision

ARCHITECTURE §8 splits every decision in two. **Firm positions** change via an issue against
that section *with a counter-proposal*, never by quietly rewording the spec. **Open RFCs** are
never resolved inside ARCHITECTURE or a capability page — RFC-006 owns multi-KB
routing/authorization, RFC-007 the permission-gate vocabulary; preserve that split.

## Build phase

Order is fixed — ARCHITECTURE §7. Each remaining step proves exactly one seam; don't build
ahead of it. Hermes is the first harness.

- **A capability is:** `CAPABILITY.md` (typed frontmatter + installer's briefing), the
  `skills/<id>/` entry skill plus focused skills, `agents/*.agent.yaml` if it needs one,
  `ONBOARDING.md` + `MOD.example.md` **as a pair or neither**, plus `kb/` and `adapters/` as needed.
- **This repo is public.** Capabilities are extracted from a live private setup, but nothing
  personal lands in a committed file: no real names, companies or relationships; no secrets; no
  actual KB content. `ONBOARDING.md` ships *questions*, `MOD.example.md` *placeholders*. Lift
  the mechanism, genericize the content; when in doubt, redact.
- **A spec gap means fixing the spec, not diverging.** Update ARCHITECTURE on `spec` via the
  firm-position discipline. A capability silently inconsistent with a contract is a bug in one
  or the other — never something to leave standing.
- **"Does it work"** = can the harness LLM, given only the capability + cheat-sheet + a fixture
  `MOD.example.md`, produce a correct install? That is the golden-render test — dogfood it on
  Hermes for real.

## Adding documents

- Match the section skeleton of the family you're adding to. New RFCs take the next number.
- Relative cross-links; inline mermaid. **Every mermaid block must parse** — a `;` inside a
  *sequence-diagram* message is a statement separator and breaks rendering (use `—`). Fine
  inside a quoted flowchart label.
- Adding or removing a capability or RFC means updating the tables that index it: §7, §8,
  Appendix A/B, and the README reading list.
- A contract no reference capability exercises gets cut (§ risk 5). Sharpen an existing section
  rather than adding one.
