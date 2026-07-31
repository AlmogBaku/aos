<div align="center">

# aos

**The batteries for your agent harness.**

Capabilities that install into the agent you already run — interview you once,
personalize themselves, and survive every upgrade.

[![CI](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml/badge.svg)](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Spec](https://img.shields.io/badge/spec-ARCHITECTURE%20v0.1-001F5C.svg)](https://github.com/AlmogBaku/aos/tree/spec)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

> [!NOTE]
> `aos` is a placeholder name — [RFC-001](https://github.com/AlmogBaku/aos/blob/spec/rfcs/RFC-001-naming.md) picks the real one.

Harnesses are batteries-not-included: OpenClaw, Hermes, or NanoClaw give you an agent,
then leave the chief-of-staff layer — knowledge base, capture, schedules, personas — for
you to hand-roll. This kit is that layer, as a **protocol plus reference implementations**:
markdown, prompts, and (where real code is needed) standalone tools behind process
boundaries. No runtime, no CLI, no rent.

> [!TIP]
> **Reading this as an agent?** Your entry point is [`BOOTSTRAP.md`](BOOTSTRAP.md) — the
> install sequence (you are the installer). It tells you when to load your harness
> runtime's [cheat-sheet](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/). Everything else here is context for your human.

## What's in the box

Built and passing the [three CI tiers](docs/TESTING.md) today:

| Capability | Type | What it does |
|---|---|---|
| [**kb**](capabilities/kb/) | infra | Multi-base knowledge infrastructure: registry, rules-first routing, the base engine (immutable `_raw/` + current-truth wiki), and the deterministic [`kb` tool](capabilities/kb/tool/) |
| [**work-tracker**](capabilities/work-tracker/) | usecase | Commitments only you can keep: filed as you speak, time blocked in the same exchange, a nightly steward keeping the backlog honest, and an exit when they are done |
| [**capability-lifecycle**](capabilities/capability-lifecycle/) | infra | The whole life of a capability, as skills in your harness: install · upgrade · remove · onboard (the interview engine → your `MOD.md`) · import (wrap what you already built) · build (a chat request that's really a use case → intake → design → approval) · contribute · evolve. Owns the household and its pinned renders, the [`aos-lock`](capabilities/capability-lifecycle/tool/) tool (lockfile + computed skill names), the per-harness cheat-sheets, and Anthropic's [`skill-creator`](https://github.com/anthropics/skills) by reference |

Planned next, in [build order](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#7-reference-capabilities--build-order) — each step proves one new seam:
**ptt-mode** (voice) ·
**interviewing** (capability-on-capability) · **news-tracker** (the "boring port") ·
**permission-gate** (capabilities that ship code) · **router** (front-door dispatch) ·
**agent-comms** (agent↔agent, glass-box).

## Install

Paste into your agent:

> Clone https://github.com/AlmogBaku/aos.git to ~/aos/upstream, read
> ~/aos/upstream/BOOTSTRAP.md, then set me up.

That's the whole funnel — there is no installer binary. Your harness's own agent performs
the install: it interviews you (identity, timezone, sacred time, red lines), writes your
answers to a `MOD.md` it will never overwrite, renders each skill against them, links the
render into your harness, creates agents and schedules per its cheat-sheet, and records
every artifact in a lockfile so removal is exact. Everything lands in one directory — the
**household**:

```text
~/aos/
├── upstream/    ← the kit clone: pristine, nothing personal ever lands here
├── personal/    ← your private repo: MOD.md files, every rendered skill, your own capabilities
├── vendor/      ← third-party skills the kit references rather than ships
└── .aos/        ← machine-local: the install lockfile
```

`upstream/` is the aos source: your install reads from it, and it's the same clone you'd
edit to contribute — so every user is one branch from being a contributor. Change it only
for what belongs to everybody (anything just for you is a `MOD.md` line in `personal/`);
forking, when you need somewhere to push, is one command (`gh repo fork --remote`). Never
a gate, and never something your agent does without asking.

> [!IMPORTANT]
> Nothing lands in your harness without your approval: the installer shows the full diff
> of every write before making it, and everything it materializes is recorded in
> `.aos/installs.lock.yaml`. No lockfile record, no artifact.

| Harness | Status |
|---|---|
| [OpenClaw](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-openclaw.md) | 🧪 cheat-sheet shipped, research-drafted — not yet e2e-verified |
| [Hermes](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-hermes.md) | ✅ supported — e2e-tested for real |
| [NanoClaw](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-nanoclaw.md) (v1 + v2) | 🧪 cheat-sheet shipped, research-drafted — not yet e2e-verified |
| [Nanobot](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-nanobot.md) | 🧪 cheat-sheet shipped, research-drafted — not yet e2e-verified |
| Claude Code | 🧪 cheat-sheet shipped, research-drafted — no runner yet |
| OpenCode | 📋 planned — BOOTSTRAP's no-cheat-sheet path works today; [contribute a sheet](CONTRIBUTING.md) |

New here? The human-facing walkthrough is [docs/INSTALL.md](docs/INSTALL.md).

## What it feels like

```text
You    ▸ capture: renew the passport before the Berlin trip
Agent  ▸ 🦜                          # your MOD.md picked that confirmation — instant, no questions

You    ▸ I need to find time to write the CFP before Friday
Agent  ▸ filed, and blocked 09:00-11:00 Thursday — outside your sacred hours.
         Sound right?                # the same exchange, not at midnight

23:00  ▸ the steward walks the backlog: the CFP block still stands, one
         commitment has slipped three times and is worth re-deciding — it asks
23:30  ▸ kb's archiver promotes what is actually knowledge into wiki pages
         (skeptical by default — most captures aren't)

You    ▸ what's on my plate for the Berlin trip?
Agent  ▸ a query, not a list file — with links into your KB, and "not in the KB"
         when it doesn't know, instead of inventing an answer
```

Capture is dumb and fast; judgment runs on schedules; recall cites its sources and admits
gaps. Day-to-day details: [docs/USAGE.md](docs/USAGE.md).

## How it works

![aos architecture: use-case capabilities compose on infra capabilities (knowledge base, capability lifecycle), which break down into skills; the user-owned MOD.md overlay sits beside them; both live in the household — upstream/, personal/, vendor/, .aos/ — and the harness LLM turns capability × MOD.md × cheat-sheet into a pinned render symlinked into your harness](docs/diagram.svg)

Seven commitments make the loop work (plain-words tour in [docs/CONCEPTS.md](docs/CONCEPTS.md)):

- **Protocol, not runtime.** A capability is a directory of skills, agent specs, schedules,
  and templates your harness's LLM installs — `install`/`update`/`remove` are conversations,
  never a program.
- **Your personalization is untouchable.** Interviews write `MOD.md` files that upstream
  never ships or merges; a `git pull` can't eat your nuances — by construction. They live
  in your own repo beside every rendered skill, so an upgrade is a git diff you review and
  a rollback is `git revert`.
- **One render, linked — never copied.** Applying your answers to a skill is judgment, so
  the result is written once into `personal/`, committed, and symlinked into your harness.
  One canonical copy means "what's installed" has exactly one answer.
- **The adapter is knowledge, not code.** Supporting a harness means writing a
  [cheat-sheet](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-hermes.md) that teaches its own LLM the mapping —
  six sections, zero glue code. And it's an aid, not a gate: with no cheat-sheet,
  BOOTSTRAP has the agent derive the mapping itself.
- **Every capability has one face.** An entry skill named after the capability is the
  runtime map; depth stays one `reference/` hop away.
- **A skill's name is single-owner.** Harnesses keep one flat skill namespace, so the name a
  skill installs under is computed (`<skill_prefix><id>`) and gated against everything
  already there — your other capabilities, the lockfile, and skills aos never installed.
- **Deterministic where it counts.** Real machinery (like kb's `kb` tool) is standalone,
  judgment-free software: files and exit codes, no LLM inside.

## Repo layout

This repo is the kit — what lands at `~/aos/upstream`, pristine (your own things live one
directory over, in `~/aos/personal`):

```text
BOOTSTRAP.md               ← agents start here (the install sequence)
CONTRIBUTING.md            ← humans with a PR start here
capabilities/<id>/         ← the built capabilities (see table above); cheat-sheets live in
                             capability-lifecycle's reference/harness-<runtime>.md, one per runtime
docs/                      ← concepts, install & usage guides, testing, gap ledger
tools/ · tests/            ← deterministic lint + golden-render checks (CI)
```

The **[`spec` branch](https://github.com/AlmogBaku/aos/tree/spec)** is the other half of
the repo: the normative [ARCHITECTURE.md](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md),
eight open [RFCs](https://github.com/AlmogBaku/aos/tree/spec/rfcs), capability one-pagers,
and design deep-dives. Main is the kit you install; spec is the paper it's built against.

## The one story to keep in mind

A team member's personal-trainer capability, built in their own Hermes: they *ask their
agent* to import it into the kit → PR → you ask your agent to install it → the interview
asks *you* (your goals, your gym days, your injuries) → your harness runs *your*
version → the author's next release merges in without touching your nuances.
**Wrap → share → install → personalize → upgrade.** Every contract in this repo exists to
make that loop work.

## Why this is open source

The harness companies — and a wave of startups on top of them — are commercializing exactly
this layer: the built-in building blocks, the chief-of-staff, the second brain. We are
builders. We build this anyway, for ourselves, on whatever harness we each run — and we're
not going to pay rent on our own work, to them or to anyone productizing it.

A chief of staff is not something that should live inside some company's proprietary IP.
It's something everybody should have. Turning it into a product is not our job; keeping it
a commons is. That's why the concepts, the contracts, and the batteries are open — MIT, one
repo, belonging to the people who build with them.

## Docs

| Doc | The question it answers |
|---|---|
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | What is a capability, an overlay, a base? — the mental model |
| [docs/INSTALL.md](docs/INSTALL.md) | What actually happens when I install this? |
| [docs/USAGE.md](docs/USAGE.md) | How do I use it day to day? |
| [BOOTSTRAP.md](BOOTSTRAP.md) | (For your agent) the exact install sequence |
| [docs/TESTING.md](docs/TESTING.md) | How is any of this tested without a runtime? |
| [docs/BUILD-GAPS.md](docs/BUILD-GAPS.md) | Where has building diverged from the spec, and what happened? |
| [Spec branch reading list](https://github.com/AlmogBaku/aos/tree/spec#readme) | The contracts themselves — normative |

## Contributing

The fastest way to move anything is to build against it — a working PR outranks an RFC
comment. Capability PRs, harness cheat-sheets, and RFC input are all wanted:
**[CONTRIBUTING.md](CONTRIBUTING.md)**.

## License

[MIT](LICENSE).
