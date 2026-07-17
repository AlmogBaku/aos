# Design deep-dive: anatomy of a capability

*Companion to ARCHITECTURE §2. This is the worked example — every file of a real capability (gtd-capture), what reads it, when, and who executes what. Where ARCHITECTURE is the contract, this is the exhibit.*

## 1. The whole repo, from the top

What a user's clone actually looks like (their machine, after installing two capabilities):

```
aos/                              # the user's clone (private fork or plain clone — RFC-005)
├── README.md                     # paste-to-install entry point (see design/install-flow.md §1)
├── ARCHITECTURE.md               # this spec
├── MOD.md                        # ★ USER-OWNED: global profile (identity, tz, hours, sacred time, red lines)
├── kb-registry.yaml              # ★ USER-OWNED: their KBs (work/personal/…)
├── .aos/                         # machine-local, gitignored
│   ├── installs.lock.yaml        # what's installed, where, versions, artifact hashes
│   ├── backups/                  # pre-upgrade snapshots
│   └── conflicts/                # parked diffs when hand-edits collide with re-renders
├── harnesses/
│   ├── hermes/CHEATSHEET.md      # per-harness install knowledge (§5.2)
│   ├── nanoclaw/CHEATSHEET.md
│   └── openclaw/CHEATSHEET.md
├── capabilities/
│   ├── kb/ …
│   └── gtd-capture/              # ↓ dissected below
│       └── MOD.md                # ★ USER-OWNED: this user's gtd nuances
├── rfcs/
└── docs/
```

★ = overlay family: upstream never contains these paths; CI rejects them in PRs.

## 2. gtd-capture, file by file

```
capabilities/gtd-capture/
├── CAPABILITY.md           # [manifest] read at INSTALL by the installing LLM
├── README.md                 # [humans + PR review] support matrix lives here
├── skills/
│   ├── capture/
│   │   ├── SKILL.md          # [runtime: MAIN agent] the fast-capture skill
│   │   └── sections/
│   │       └── entry-format.md   # loaded on demand by SKILL.md (keeps preamble small)
│   ├── drain/
│   │   ├── SKILL.md          # [runtime: DRAINER agent only] nightly promotion logic
│   │   └── drain-prompt.md   # the schedule's prompt body (referenced by manifest)
│   └── format-entry/
│       └── SKILL.md          # [runtime: both] shared entry-format helper
├── agents/
│   └── drainer.agent.yaml    # [install] neutral spec → Hermes profile / NanoClaw group / …
├── ONBOARDING.md            # [install + re-runs] frontmatter = typed questions (also validates
│                             #   MOD.md); body = the interview script. Same shape as CAPABILITY.md
├── MOD.example.md          # [install] shipped seed copied to MOD.md before the interview fills it
├── kb/
│   └── zones/inbox.md.tmpl   # [install] zone template registered into the target KB
└── MOD.md                    # ★ [everything, at render time] this user's nuances
                             #   (created here at install from MOD.example.md; never shipped upstream)
```

**Who reads what, when:**

| Moment | Actor | Reads | Writes |
|---|---|---|---|
| Install | harness LLM (installer role) | CAPABILITY.md, cheat-sheet, MOD.md (after interview) | harness artifacts, lockfile |
| Install (interview) | onboarding capability | ONBOARDING.md, MOD.example.md | MOD.md, harness secret store |
| Runtime (capture) | main agent | rendered capture skill (which embeds MOD.md nuances) | routed KB inbox |
| Runtime (drain, 23:00) | drainer agent | rendered drain skill, KB zone | KB zones, log.md |
| Upgrade | harness LLM (merge role) | new upstream files, current render, MOD.md | new render (diff-reviewed), lockfile, backups |
| Lint/CI | repo CI | everything except overlay family | PR status |

## 3. Template vs page: the same skill, before and after

**Shipped** (`skills/capture/SKILL.md`, upstream — the *template*; personalization slots are declared, empty):

```markdown
---
name: capture
description: Instant capture to inbox. Never classify synchronously; capture is dumb and fast.
---
Capture the user's item verbatim into the routed KB inbox (see kb router).
Apply the user's capture preferences from MOD.md: {{mod: capture_preferences}}
Format per sections/entry-format.md. Confirm with a single emoji, nothing more.
```

**Installed in this user's Hermes** (the *page* — what the LLM actually materialized into `~/.hermes/skills/gtd-capture-capture/`, origin-tagged, hash in lockfile):

```markdown
---
name: capture
description: Instant capture to inbox. Never classify synchronously; capture is dumb and fast.
x-aos-origin: gtd-capture@0.1.0        # attribution tag — doctor/remove/round-trip use this
---
Capture the user's item verbatim into the routed KB inbox.
User preferences (from MOD.md): voice notes get transcribed then captured raw; anything
mentioning the company or clients hints work-KB; captures after 22:00 default to personal.
Format per entry-format section. Confirm with 👍 only — the user hates chatty confirmations.
```

The `{{mod: …}}` slot is a *convention, not a template engine* — it marks where the installing LLM weaves overlay content in. The transform is agentic (§3.2); the slot just tells it where the seams are.

## 4. Where each declared thing lands (Hermes example)

| Declaration in CAPABILITY.md | Becomes (per Hermes cheat-sheet) |
|---|---|
| `skills: capture, used_by: [main]` | `~/.hermes/skills/gtd-capture-capture/` in the **root profile only** |
| `skills: drain, used_by: [drainer]` | skill in the **drainer profile's workspace only** — the main agent never sees it |
| `agents: drainer.agent.yaml` | `~/.hermes/profiles/gtd-drainer/` + entry in `config.yaml` |
| `schedules: nightly-drain` | entry in `~/.hermes/cron/jobs.json`, `origin: aos:gtd-capture@0.1.0`, assigned to profile `gtd-drainer` — **in exactly one harness** (single-owner rule, §5.5) |
| `kb: zones: ops/inbox.md` | row appended to the target KB's `AGENTS.md` zone table (a grant, §4.3) + zone file seeded from `kb/zones/inbox.md.tmpl` |
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
