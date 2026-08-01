<div align="center">

# aos

*Memory and follow-through for the agent you already run.*

[![CI](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml/badge.svg)](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![Spec](https://img.shields.io/badge/spec-ARCHITECTURE%20v0.1-001F5C.svg?style=flat-square)](https://github.com/AlmogBaku/aos/tree/spec)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)

[What you get](#what-you-get) • [Install](#install) • [How it works](#how-it-works) • [Harnesses](#harness-support) • [Docs](#docs)

</div>

Your agent can hold a conversation, but it forgets what you told it last week, doesn't track
what you said you'd do, and does nothing while you sleep. Everyone builds that layer
themselves, once per harness.

This is that layer, packaged. Ask your agent to install it and you get a **knowledge base**
that files what you say and answers questions about it later, and a **commitment tracker**
that blocks time for things you promised. It interviews you once, and keeps your answers when
the kit updates.

There is nothing to run — no daemon, no CLI, no service. A capability is markdown your agent
reads, plus a small tool with no LLM in it wherever something has to be exact.

## What you get

| | |
|---|---|
| [**kb**](capabilities/kb/) | Say something worth keeping and it's filed — no form, no questions. Ask later and you get an answer *with sources*, or an honest "not in the KB". Several bases (personal, work) with rules deciding what lands where. |
| [**work-tracker**](capabilities/work-tracker/) | *"I need to write the CFP by Friday"* becomes a tracked commitment with time blocked for it, in the same exchange. A nightly pass finds what slipped and asks about it. |
| [**capability-lifecycle**](capabilities/capability-lifecycle/) | The machinery for the above: install, upgrade, remove, the interview — and wrapping something you already built into a capability worth sharing. |

Two properties that shape daily use:

- **Capture is fast; judgment is scheduled.** Filing a thought never blocks on a question. The
  passes that need thinking run overnight, where waiting is free.
- **Recall admits gaps.** Answers cite their sources, and "not in the KB" beats a confident
  invention.

## Install

Paste this to your agent:

> Clone https://github.com/AlmogBaku/aos.git to ~/aos/upstream, read
> ~/aos/upstream/BOOTSTRAP.md, then set me up.

That's the whole funnel. Your own agent does the work: it interviews you (identity, timezone,
sacred hours, red lines), writes your answers somewhere it will never overwrite, wires the
skills into your harness, and records every artifact so removal is exact.

> [!IMPORTANT]
> Nothing lands without your approval. You see the full diff of every write before it happens,
> and everything installed is recorded — no record, no artifact. Removal walks that record
> backwards.

Prerequisites: `git`, [`uv`](https://docs.astral.sh/uv/), and an agent harness. Walkthrough of
what actually happens: [docs/INSTALL.md](docs/INSTALL.md).

> [!TIP]
> **Reading this as an agent?** Clone first, then follow the *local* copy at
> `~/aos/upstream/BOOTSTRAP.md` — it reads files out of the clone, so working from this web
> page strands you two steps in.

## How it works

![aos architecture: use-case capabilities compose on infrastructure capabilities, which break down into skills; your answers sit beside them in your own repo; the harness LLM combines capability, answers and a per-harness cheat-sheet into a pinned render linked into your harness](docs/diagram.svg)

**A capability is a directory, not a program.** Skills, agent specs, schedules, templates.
Installing one is a conversation — nothing is left running afterwards.

**Your answers live apart from the kit, so upgrades can't eat them.** They go in *your* repo.
Upstream never ships that file and never merges it, so `git pull` cannot touch it. An upgrade
re-applies your answers to the new version and shows you the diff; undoing one is `git revert`.

**Supporting a new harness means writing a document, not code.** Six sections that teach that
harness's own LLM how the concepts map onto its primitives — no adapter, no plugin, no glue.
Without one, your agent works the mapping out itself.

**Anything that must be exact is exact.** Names, hashes and layout come from a judgment-free
tool: files and exit codes, no LLM inside. Everything needing taste stays with the agent.

Plain-words tour of the model: [docs/CONCEPTS.md](docs/CONCEPTS.md).

## Harness support

| Harness | Status |
|---|---|
| [Hermes](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-hermes.md) | Supported — verified by a real install, not a simulation |
| [OpenClaw](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-openclaw.md) | Cheat-sheet shipped, research-drafted — not yet verified end to end |
| [NanoClaw](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-nanoclaw.md) (v1 + v2) | Cheat-sheet shipped, research-drafted |
| [Nanobot](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-nanobot.md) | Cheat-sheet shipped, research-drafted |
| [Claude Code](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-claude-code.md) | Cheat-sheet shipped, research-drafted |
| OpenCode | Planned — the no-cheat-sheet path works today |

> [!NOTE]
> "Research-drafted" means the mapping was written from the harness's docs but no real install
> has run against it. It is marked that way until someone runs one — [adding a
> sheet](CONTRIBUTING.md) is one document.

Planned capabilities, in [build order](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#7-reference-capabilities--build-order)
— each proves one new seam: **ptt-mode** (voice) · **interviewing** (capability-on-capability)
· **news-tracker** (the boring port) · **permission-gate** (capabilities that ship code) ·
**router** (front-door dispatch) · **agent-comms** (agent↔agent, glass-box).

## Why this exists

A chief of staff shouldn't live inside a company's proprietary IP. The harness vendors — and a
wave of startups on top of them — are commercializing exactly this layer. We build it anyway,
for ourselves, on whatever harness we each run, and we're not paying rent on our own work.

The loop every contract here exists to serve: someone builds a personal-trainer capability in
their own harness → asks their agent to wrap it → PR → you ask your agent to install it → the
interview asks *you*, about your goals and your injuries → you run *your* version → their next
release merges in without touching your answers.

## Repo layout

This repo is the kit — what lands at `~/aos/upstream`. Your own things live one directory over.

```text
BOOTSTRAP.md          the install sequence (agents start here, from the clone)
capabilities/<id>/    the built capabilities; per-harness cheat-sheets live inside
                      capability-lifecycle's reference/
docs/                 concepts, install and usage guides, testing, the gap ledger
tools/ · tests/       the lint, the gates, and the golden-render checks CI runs
```

The [`spec` branch](https://github.com/AlmogBaku/aos/tree/spec) is the other half:
[ARCHITECTURE.md](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md) (normative), the
open [RFCs](https://github.com/AlmogBaku/aos/tree/spec/rfcs), capability one-pagers and design
deep-dives. Main is the kit you install; spec is the paper it's built against.

> [!NOTE]
> `aos` is a placeholder name — [RFC-001](https://github.com/AlmogBaku/aos/blob/spec/rfcs/RFC-001-naming.md)
> picks the real one.

## Docs

| Doc | The question it answers |
|---|---|
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | What is a capability, an overlay, a base? |
| [docs/INSTALL.md](docs/INSTALL.md) | What actually happens when I install this? |
| [docs/USAGE.md](docs/USAGE.md) | How do I use it day to day? |
| [docs/TESTING.md](docs/TESTING.md) | How is any of this tested without a runtime? |
| [docs/BUILD-GAPS.md](docs/BUILD-GAPS.md) | Where has building diverged from the spec? |
| [BOOTSTRAP.md](BOOTSTRAP.md) | (For your agent) the exact install sequence |
