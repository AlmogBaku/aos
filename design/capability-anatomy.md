# Design deep-dive: anatomy of a capability

*Companion to ARCHITECTURE §2. This is the worked example — every file of a real capability (gtd-capture), what reads it, when, and who executes what. Where ARCHITECTURE is the contract, this is the exhibit.*

> **Anatomy note (2026-07-24):** gtd-capture has migrated to the entry-skill convention
> ARCHITECTURE §2 gained during the kb redesign (§2.5, the five-building-blocks
> lifecycle, skill-bundled assets, `exec:` schedules, agent prompt bodies co-located
> under `agents/<name>/`). This exhibit reflects its current shape; `kb` remains the
> first conforming example (design/kb-methodology.md §10).

## 1. The whole repo, from the top

What a user's clone actually looks like (their machine, after installing two capabilities):

```
aos/                              # the user's clone (private fork or plain clone — RFC-005)
├── README.md                     # paste-to-install entry point (see design/install-flow.md §1)
│                                 # (spec docs — ARCHITECTURE.md, design/, rfcs/ — live on the spec BRANCH, not in the main clone)
├── MOD.md                        # ★ USER-OWNED: global profile (identity, tz, hours, sacred time, red lines)
├── kb-registry.yaml              # ★ USER-OWNED: their KBs (work/personal/…)
├── .aos/                         # machine-local, gitignored
│   ├── installs.lock.yaml        # what's installed, where, versions, artifact hashes
│   ├── backups/                  # pre-upgrade snapshots
│   └── conflicts/                # parked diffs when hand-edits collide with re-renders
├── harnesses/
│   ├── hermes.md                 # per-harness cheat-sheets, flat, named for the
│   ├── nanoclaw.md               #   harness runtime (§5.2)
│   ├── openclaw.md
│   └── nanobot.md
├── capabilities/
│   ├── kb/ …
│   └── gtd-capture/              # ↓ dissected below
│       └── MOD.md                # ★ USER-OWNED: this user's gtd nuances
└── docs/
```

★ = overlay family: upstream never contains these paths; CI rejects them in PRs.

## 2. gtd-capture, file by file

```
capabilities/gtd-capture/
├── CAPABILITY.md           # [manifest] read at INSTALL by the installing LLM
├── README.md                 # [humans + PR review] support matrix lives here
├── skills/
│   ├── gtd-capture/           # the ENTRY SKILL — front door, used_by BOTH main + drainer
│   │   ├── SKILL.md          #   mental model, where things live, routing table to the
│   │   │                     #   two narrower skills below, authority tiers
│   │   └── reference/
│   │       └── entry-format.md   # on-demand depth: what capture composes, corrections rule
│   ├── capture/
│   │   └── SKILL.md          # [runtime: MAIN agent only] the fast-capture skill
│   └── drain/
│       └── SKILL.md          # [runtime: DRAINER agent only] nightly GTD triage — stays a
│                             #   real loadable skill (also user-triggerable ad hoc, not
│                             #   only the schedule)
├── agents/
│   ├── drainer.agent.yaml    # [install] neutral spec → Hermes profile / NanoClaw group / …
│   └── drainer/
│       └── nightly-drain.md  # the schedule's prompt body, co-located with its agent spec
│                             #   (§2.1) — a thin kickoff into the drain skill, not a copy of it
├── ONBOARDING.md            # [install + re-runs] frontmatter = typed questions (also validates
│                             #   MOD.md); body = the interview script. Same shape as CAPABILITY.md
├── MOD.example.md          # [install] shipped seed copied to MOD.md before the interview fills it
├── kb/
│   └── zones/next-actions.md.tmpl   # [install] standalone-next-actions template — a grant
│                                     #   into kb's EXISTING `_ops/` zone, not a new zone of
│                                     #   its own (kb is infra; usecase capabilities build on
│                                     #   its already-declared zones)
└── MOD.md                    # ★ [everything, at render time] this user's nuances
                             #   (created here at install from MOD.example.md; never shipped upstream)
```

Note what's gone relative to the pre-migration layout: no `ops/inbox.md` zone (captures
land in kb's own `raw/captures/`, which kb's install already grants the front agent
`route-into` on) and no `format-entry` skill (its whole job — hand-rolled line format,
tag-append rules — is now the `base capture` tool's frontmatter, for free).

**Who reads what, when:**

| Moment | Actor | Reads | Writes |
|---|---|---|---|
| Install | harness LLM (installer role) | CAPABILITY.md, cheat-sheet, MOD.md (after interview) | harness artifacts, lockfile |
| Install (interview) | onboarding capability | ONBOARDING.md, MOD.example.md | MOD.md, harness secret store |
| Runtime (capture) | main agent | rendered capture skill (which embeds MOD.md nuances) | a raw file in the routed KB's `raw/captures/`, via kb's `base capture` (sha256 dedup, `triage: pending` come free) |
| Runtime (drain, 23:00) | drainer agent | rendered drain skill; kb's pending view (`base inbox` / `base inbox --failed`) | next-actions (a project's `next_action` field, or `_ops/next-actions.md`), reminders, `meta.gtd_triaged` on the capture — never the capture's own `triage` field, which stays kb's archiver's call at its later 23:30 promote step |
| Upgrade | harness LLM (merge role) | new upstream files, current render, MOD.md | new render (diff-reviewed), lockfile, backups |
| Lint/CI | repo CI | everything except overlay family | PR status |

## 3. Template vs page: the same skill, before and after

**Shipped** (`skills/capture/SKILL.md`, upstream — the *template*; personalization slots are declared, empty):

```markdown
---
name: capture
description: Instant capture, no classification. Use when the user fires off a thought, task, idea, or voice note to capture — never classify synchronously; capture is dumb and fast.
---
1. Resolve the target KB with kb's `route` skill. Never ask the user where it goes.
2. Write it: `base --base <name> capture --text <verbatim content> --source <channel>`
   — frontmatter, sha256 dedup, `triage: pending`, and the log line come free from the
   tool. Content verbatim — no cleanup, no summarizing.
3. A correction to something already captured is a new capture, never an edit — see
   [../gtd-capture/reference/entry-format.md](../gtd-capture/reference/entry-format.md).
4. Apply the user's capture preferences from MOD.md: {{mod: capture_preferences}}
5. Confirm with a single emoji. No echo, no follow-up questions.
```

**Installed in this user's Hermes** (the *page* — what the LLM actually materialized into `~/.hermes/skills/gtd-capture-capture/`, origin-tagged, hash in lockfile):

```markdown
---
name: capture
description: Instant capture, no classification. Use when the user fires off a thought, task, idea, or voice note to capture — never classify synchronously; capture is dumb and fast.
x-aos-origin: gtd-capture@0.2.0        # attribution tag — doctor/remove/round-trip use this
---
1. Resolve the target KB with kb's `route` skill. Never ask the user where it goes.
2. Write it: `base --base <name> capture --text <verbatim content> --source <channel>`
   — frontmatter, sha256 dedup, `triage: pending`, and the log line come free from the tool.
3. A correction to something already captured is a new capture, never an edit — see
   [../gtd-capture/reference/entry-format.md](../gtd-capture/reference/entry-format.md).
4. User preferences (from MOD.md): voice notes get transcribed then captured raw; anything
   mentioning the company or clients hints work-KB; captures after 22:00 default to personal.
5. Confirm with 👍 only — the user hates chatty confirmations.
```

The `{{mod: …}}` slot is a *convention, not a template engine* — it marks where the installing LLM weaves overlay content in. The transform is agentic (§3.2); the slot just tells it where the seams are.

## 4. Where each declared thing lands (Hermes example)

| Declaration in CAPABILITY.md | Becomes (per Hermes cheat-sheet) |
|---|---|
| `skills: capture, used_by: [main]` | `~/.hermes/skills/gtd-capture-capture/` in the **root profile only** |
| `skills: drain, used_by: [drainer]` | skill in the **drainer profile's workspace only** — the main agent never sees it |
| `agents: drainer.agent.yaml` | `~/.hermes/profiles/gtd-drainer/` (directory-defined — `hermes profile create`; no config.yaml registry) |
| `schedules: nightly-drain` | entry in `~/.hermes/cron/jobs.json`, name-prefixed `aos:gtd-capture:nightly-drain` (§5.3 — `jobs.json`'s own `origin` field means chat provenance, not this), assigned to profile `gtd-drainer` — **in exactly one harness** (single-owner rule, §5.5) |
| `kb: zones: _ops/next-actions.md` | row appended to the target KB's `AGENTS.md` zone table (a grant, §4.3) — nested inside kb's *own* `_ops/` zone, not a new top-level dir — + zone file seeded from `kb/zones/next-actions.md.tmpl` |
| `secrets` in MOD.md frontmatter | values in `~/.hermes/auth.json`; MOD.md holds only `{store, key}` refs |

Skill scoping is the load-bearing row: **`used_by` is what keeps ten capabilities from becoming fifty skills in every agent's context.** The drainer carries drain logic; the front agent carries capture only.

## 5. What the lockfile knows

```yaml
# .aos/installs.lock.yaml (machine-local)
installs:
  gtd-capture:
    version: 0.1.0
    onboarded: 2026-07-17
    harnesses:
      hermes:
        artifacts:
          - path: ~/.hermes/skills/gtd-capture-capture/SKILL.md
            hash: sha256:…
          - path: ~/.hermes/profiles/gtd-drainer/
            hash: sha256:…            # dir-tree hash
          - path: ~/.hermes/cron/jobs.json#nightly-drain   # keyed entry in a shared file
            hash: sha256:…
        schedules_owned: [nightly-drain]   # single-owner rule: this harness runs the drain
      nanoclaw:
        artifacts: [ …capture skill only… ]
        schedules_owned: []                # installed here too, but the drain runs in Hermes
```

Hashes exist so `doctor` can tell *"you hand-edited the rendered skill"* (→ round-trip it into MOD.md, §3.3) apart from *"the render is what we wrote"* — without them, drift is invisible and the overlay rots (risk #4).
