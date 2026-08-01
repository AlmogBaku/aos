# Design deep-dive: anatomy of a capability

*Companion to ARCHITECTURE §2. This is the worked example — every file of a real capability (work-tracker), what reads it, when, and who executes what. Where ARCHITECTURE is the contract, this is the exhibit.*

> **Anatomy note (2026-07-29):** this exhibit was cut against `gtd-capture`, which
> **work-tracker replaces** (it absorbed `time-blocking` with it — finding time for a
> commitment is not a separate capability from making one, ARCHITECTURE §7). Re-cut here
> against the real work-tracker package, so the worked example is a capability that exists.
> Two things the old cut got wrong beyond the rename, worth naming because an exhibit is
> copied: it reproduced one skill description **verbatim twice** as the canonical good
> example — including a `description` that stated only what the skill did and never when to
> use it — and it drew a KB grant into a zone (`_ops/`) that no longer exists.

## 1. The whole household, from the top

What a user's machine actually looks like (after installing two capabilities) — the **household** (§3.1):

```
~/aos/                            # the household — a plain directory, itself never a git repo
├── upstream/                     # the kit clone: pristine, contributor-shaped (origin = fork,
│   │                             #   upstream = canonical); NOTHING personal in it, ever
│   ├── README.md                 # paste-to-install entry point (see design/install-flow.md §1)
│   │                             # (spec docs — ARCHITECTURE.md, design/, rfcs/ — live on the spec BRANCH)
│   ├── BOOTSTRAP.md              # the agent's door: warm stub — prereqs, household creation,
│   │                             #   one inline install, hand-over (install-flow §1)
│   ├── capabilities/
│   │   ├── capability-lifecycle/
│   │   │   └── skills/capability-lifecycle/reference/
│   │   │       ├── harness-hermes.md   # per-harness cheat-sheets: reference files of the
│   │   │       └── …                   #   entry skill that reads them, so they travel
│   │   │                               #   with the render (§5.2)
│   │   ├── kb/ …
│   │   └── work-tracker/         # ↓ dissected below (the TEMPLATE — never edited)
│   └── docs/
├── personal/                     # ★ USER-OWNED: their ONE private repo — "my aos, as built"
│   ├── MOD.md                    # global profile (identity, tz, hours, sacred time, red lines)
│   ├── kb-registry.yaml          # their KBs (work/personal/…)
│   └── capabilities/
│       ├── work-tracker/         # personalized twin of upstream/capabilities/work-tracker/
│       │   ├── MOD.md            # this user's deltas from the shipped defaults
│       │   └── skills/…          # the PINNED RENDER (§3.1) — tracked; harnesses symlink here
│       └── my-private-cap/       # private capabilities: full §2.1 package + MOD + render
└── .aos/                         # machine-local state, outside every repo
    ├── installs.lock.yaml        # what's installed: versions, source roots, links, hashes
    └── kb-principal.yml          # kb's tool writes this itself on first use: who this
                                  #   machine's humans are. Machine-local, so it is
                                  #   recreated rather than carried between machines
```

★ = the personal root holds the overlay family: upstream never contains those paths; CI rejects them in PRs.

## 2. work-tracker, file by file

```
upstream/capabilities/work-tracker/
├── CAPABILITY.md            # [manifest] read at INSTALL by the installing LLM
├── README.md                # [humans + PR review] support matrix lives here
├── skills/
│   ├── work-tracker/        # the ENTRY SKILL — front door, used_by BOTH main + steward
│   │   ├── SKILL.md         #   the one distinction everything rests on (whose work is
│   │   │                    #   it), the four statuses, a routing table to the three
│   │   │                    #   narrower skills, and who may change what without asking
│   │   └── reference/
│   │       └── action-page.md   # on-demand depth: the page shape, field by field
│   ├── capture/             # installs as `wt-capture` (skill_prefix: wt-)
│   │   └── SKILL.md         # [runtime: MAIN agent] file the commitment, hand off
│   ├── schedule/            # installs as `wt-schedule`
│   │   └── SKILL.md         # [runtime: MAIN agent] find real hours, in the same exchange
│   ├── update/              # installs as `wt-update`
│   │   └── SKILL.md         # [runtime: MAIN agent] progress, blocked, done
│   └── steward/
│       └── SKILL.md         # [runtime: STEWARD agent only] the nightly maintenance pass —
│                            #   a real loadable skill, so it is also user-triggerable ad
│                            #   hoc, not reachable only through the schedule
├── agents/
│   ├── steward.agent.yaml   # [install] neutral spec → Hermes profile / NanoClaw group / …
│   └── steward/
│       └── nightly-steward.md  # the schedule's prompt body, co-located with its agent spec
│                            #   (§2.1) — a thin kickoff into the steward skill, not a copy
├── ONBOARDING.md            # [install + re-runs] frontmatter = typed questions (also validates
│                            #   MOD.md); body = the interview script. Same shape as CAPABILITY.md
├── MOD.example.md           # [install] shipped seed copied to MOD.md before the interview fills it
└── kb/
    └── zones/actions.AGENTS.md.tmpl  # [install] the zone contract for `actions/**` — prose
                                      #   the writing agents read. The zone itself must ALSO
                                      #   be declared in the base's .kb/base.yml, or every
                                      #   verb treats the directory as nonexistent
```

Five skills, one agent, one schedule, one zone. **The count is the point of the exhibit**: a
usecase capability is small, and everything it needs to say about itself fits in a manifest
plus an entry skill.

The user's side lives in the personal root, mirrored: `personal/capabilities/work-tracker/MOD.md` (★ the overlay — seeded from `MOD.example.md` at install, filled by the interview, never shipped upstream) next to `personal/capabilities/work-tracker/skills/…` (the pinned render the transform writes and harnesses link to).

Note what a usecase capability does **not** ship. No queue file of its own: "what's next" is
`kb find --where status=next`, a view over pages that each carry their own state, so there is
nothing to fall out of date. No format skill: the page shape is `kb`'s frontmatter contract
plus one reference file, not hand-rolled line rules. And no ordering contract with kb — the
steward and kb's archiver run at different hours because each is independently correct, not
because one waits for the other. An undeclared ordering assumption is the kind of thing that
rots silently when the other side changes.

**Who reads what, when:**

| Moment | Actor | Reads | Writes |
|---|---|---|---|
| Install | harness LLM (installer role) | CAPABILITY.md, cheat-sheet, MOD.md (after interview) | pinned render in `personal/` (committed), harness symlinks + native injections, lockfile |
| Install (interview) | `capability-onboard` (capability-lifecycle) | ONBOARDING.md, MOD.example.md | MOD.md, harness secret store |
| Runtime (capture) | main agent | rendered `wt-capture` skill (which embeds MOD.md nuances) | an action page under `actions/` in the commitments base, via `kb set` — one attributed commit, then a hand-off to `wt-schedule` in the SAME exchange |
| Runtime (steward, 23:00) | steward agent | rendered `wt-steward` skill; five `kb find --where` queries plus one `--without block` backstop | its own bookkeeping only — an extended `expires`, a recorded stall, a rescheduled block it created, an incremented `slipped`. Anything the user committed to is a question, not a write |
| Upgrade | harness LLM (re-render role) | new upstream files, MOD.md (the user's deltas; current render is a drift source only, §3.4) | new pinned render (reviewed as a git diff in `personal/`, commit = accept), lockfile |
| Lint/CI | repo CI | everything except overlay family | PR status |

## 3. Template vs page: the same skill, before and after

**Shipped** (`skills/capture/SKILL.md`, upstream — the *template*; the id is capability-local, personalization slots are declared and empty):

```markdown
---
name: capture
description: "Records something the user has said they must do themselves: classifies the
  commitment as next, waiting, someday or trivial, writes it as an action page in their
  commitments base, and hands off to wt-schedule when it needs real hours. Use when the user
  commits to work of their own — \"I need to find time to…\", \"I have to…\", \"remind me
  to…\", \"put that on my list\". Do NOT use when the user asks the assistant to do the work
  (\"write the CFP\", \"research X\") — that is a request to act now, not a commitment to
  track. Do NOT use for thoughts, facts or notes carrying no commitment; those are knowledge
  and belong to kb-capture."
---
1. Clarify against one question — *is this mine to do?* — and set `status:` to exactly one of
   `next` · `waiting` · `someday` · `done`. Nothing validates it, so a fifth word is written
   happily and then matches no query the steward runs.
2. Write the page: `kb --base commitments set actions/<slug>.md status=next estimate=2h`
   after creating it, or `kb capture` for the free-text path. One attributed commit either way.
3. Hand off to `wt-schedule` when it needs real hours — in the SAME exchange, never at
   midnight.
4. Apply the user's capture preferences from MOD.md: {{mod: capture_preferences}}
5. Confirm in one line. No echo, no follow-up questions.
```

**Installed for this user** (the *page* — what `aos-cap render` materialized into `personal/capabilities/work-tracker/skills/wt-capture/` and the LLM then personalized: the render directory, the frontmatter `name`, and the symlink all carry the **installed name**, committed there and symlinked from the harness):

```markdown
---
name: wt-capture                         # the installed name — rewritten by the render
description: "Records something the user has said they must do themselves: … (unchanged —
  the description is the trigger, so the transform leaves it alone unless a MOD answer
  genuinely narrows the skill's scope)"
metadata:
  aos:
    origin: work-tracker@0.1.0           # attribution — remove/verify/round-trip read this,
                                         #   and it lives in SKILL.md's own extension hatch
---
1. Clarify against one question — *is this mine to do?* — and set `status:` to exactly one of
   `next` · `waiting` · `someday` · `done`.
2. Write the page: `kb --base commitments …` — one attributed commit.
3. Hand off to `wt-schedule` when it needs real hours, in the same exchange.
4. User preferences (from MOD.md): anything mentioning the company or clients is work;
   never block before 09:00 or after 18:00; Thursdays are out entirely.
5. Confirm in one line — the user hates chatty confirmations.
```

The `{{mod: …}}` slot is a *convention, not a template engine* — it marks where the installing LLM weaves overlay content in. The transform is agentic (§3.2); the slot just tells it where the seams are.

## 4. Where each declared thing lands (Hermes example)

| Declaration in CAPABILITY.md | Becomes (per Hermes cheat-sheet) |
|---|---|
| `skills: capture, used_by: [main]` | symlink `~/.hermes/skills/wt-capture` → the pinned render, in the **root profile only** |
| `skills: steward, used_by: [steward]` | symlink in the **steward profile's skills dir only** — the main agent never sees it |
| `agents: steward.agent.yaml` | `~/.hermes/profiles/aos-steward/` (directory-defined — `hermes profile create`; no config.yaml registry) |
| `schedules: nightly-steward` | entry in `~/.hermes/cron/jobs.json`, name-prefixed `aos:work-tracker:nightly-steward` (§5.3 — `jobs.json`'s own `origin` field means chat provenance, not this), assigned to profile `aos-steward` — **in exactly one harness** (single-owner rule, §5.5) |
| `kb: zones: actions/**` | **two** things, and missing either is silent: a row appended to the target base's `AGENTS.md` grants table (§4.3) seeded from `kb/zones/actions.AGENTS.md.tmpl`, **and** a `zones:` entry plus its `type` in the base's `.kb/base.yml`. Without the second, every verb treats `actions/` as nonexistent — `find` returns nothing and `lint` says nothing, both at exit 0. The grant rows also need `index.md`, because kb seeds that to the archiver alone and both writing agents rebuild the index |
| `secrets` in MOD.md frontmatter | values in the Hermes `.env` (root or profile — `auth.json` is Hermes's own provider-credential state, never written by installs); MOD.md holds only `{store, key}` refs |

Skill scoping is the load-bearing row: **`used_by` is what keeps ten capabilities from becoming fifty skills in every agent's context.** The steward carries the maintenance pass; the front agent carries capture, scheduling and updates — the three things that happen while the user is present.

## 5. What the lockfile knows

```yaml
# <home>/.aos/installs.lock.yaml (machine-local, household level — spans source roots)
# One entry per capability, covering every harness it is installed into. `record`
# replaces an entry wholesale, so a second-harness install re-records the combined set.
installs:
  work-tracker:
    version: 0.1.0
    source_root: upstream            # which distribution shipped the package
    artifacts:                       # path -> sha256 (render files + native artifacts)
      <HOME>/aos/personal/capabilities/work-tracker/skills/wt-capture/SKILL.md: sha256:…
      <HOME>/.hermes/profiles/aos-steward/SOUL.md: sha256:…
    links:                           # harness symlink -> the pinned render it points at
      <HOME>/.hermes/skills/wt-capture: <HOME>/aos/personal/capabilities/work-tracker/skills/wt-capture
      <HOME>/.hermes/profiles/aos-steward/skills/wt-steward: <HOME>/aos/personal/capabilities/work-tracker/skills/wt-steward
    schedules_owned: [nightly-steward]  # single-owner rule: this install runs the pass
    config_keys: []
    env_lines: []
    scripts: []
```

Machine-local files a capability's own tool writes (kb's `kb-principal.yml`) are **not**
recorded: they are not materialized artifacts, so hashing one would report drift the first
time the tool touched it. Removal offers to delete them instead of walking them backwards.

Only *files* carry hashes (`sha256()` refuses a directory); links are recorded as
path→target and checked structurally — `verify` reports MISSING / NOT A LINK (a copy
where a link belongs) / RELINKED / DANGLING. Keyed entries in harness-owned files
(a `jobs.json` job) are tracked by `schedules_owned` id, not by hash.

Hashes exist so `aos-cap verify` can tell *"you hand-edited the rendered skill"* (→ round-trip it into MOD.md, §3.3) apart from *"the render is what we wrote"* — without them, drift is invisible and the overlay rots (risk #4).
