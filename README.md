<div align="center">

# aos

*The batteries for your agent harness.*

[![CI](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml/badge.svg)](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![Spec](https://img.shields.io/badge/spec-ARCHITECTURE%20v0.1-001F5C.svg?style=flat-square)](https://github.com/AlmogBaku/aos/tree/spec)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)

[The capability](#the-capability) • [What's included](#whats-included) • [Compare](#how-this-compares) • [Install](#install) • [Any harness](#one-capability-any-harness) • [Docs](#docs)

</div>

**Harnesses are batteries-not-included.** Hermes, OpenClaw, NanoClaw, Claude Code — each hands
you an agent and its own way of doing skills, personas, schedules and secrets. Personal harnesses
read as chatbots, but they're runtimes: a chat message can seed a cron, a persona, a standing
automation. Anything durable you build lands as loose files wired into one harness by hand, with
no way to package it, share it, or move it.

**This kit is the batteries.** Not a framework — two things: a **protocol** for how you ship a
capability, change it, and keep it updated, and a set of **implementations** built on it. There is
no runtime, no daemon, no service. The new software is a prompt.

And the batteries are a commons. Harness vendors and a wave of startups are commercializing
exactly this layer; we build it anyway, for ourselves, on whatever harness we each run. A personal
chief of staff shouldn't be anyone's proprietary IP.

## The capability

The protocol has one noun. A **capability** is an installable package — **think a distro package,
apt for your agent.** It declares what must exist, and your agent performs it, records it, and can
reverse it. Five building blocks:

| Block | What it is |
|---|---|
| **Skills** | knowledge your agent loads on demand — portable [Agent Skills](https://agentskills.io) folders |
| **Agents** | personas that run scheduled or delegated work |
| **Tools** | real commands on PATH — deterministic, no LLM inside. This is also how one capability reaches another: a process boundary, not a shared prompt |
| **Schedules** | crons, either agent-driven or script-direct |
| **Patches** | harness modifications, where genuinely unavoidable |

Installing one is a **conversation, not a command** — `install`, `update` and `remove` are things
you say, and your harness's own LLM does the work. No external program installs anything; the only
thing a tool ever touches is bookkeeping, hashes and diffs.

**And the shipped capability is not the installed one.** Upstream ships a template; your harness
runs *your* version of it. An interview asks how you want it to behave, your answers go in a repo
you own, and the install is always reconstructible as `template × your answers`. That transform —
not the file format — is where the whole product lives:

- Upstream never ships, writes or merges your answers. `git pull` cannot reach them.
- An upgrade re-runs the same transform against the new version. The review gate is a git diff in
  your own repo: commit to accept, `git revert` to roll back.
- Edit the installed thing by hand and your agent folds the change back into your answers, so the
  next upgrade keeps it.

Capabilities come in two kinds, and the manifest says which:

- **Infrastructure** (`tags: [infra]`) — the substrate other capabilities layer on. A knowledge
  base to serve data from. The lifecycle that installs things. Soon: agents talking to each
  other. Build one of these and everything above it gets cheaper.
- **Use-case** (`tags: [usecase]`) — solves one problem for you, by composing the layers below.

That layering is the whole point. `work-tracker` is under 900 lines of markdown and YAML — five
skills, one agent, one schedule. It has no storage engine, no retrieval, no queue file and no
installer of its own, because the two infra capabilities beneath it already have those. Its
steward calls `kb find --where status=next` as a shell command; it never loads a kb skill.

## What's included

The batteries. Three today, more coming.

**Infrastructure — what you build on:**

| | |
|---|---|
| [**capability-lifecycle**](capabilities/capability-lifecycle/) | The lifecycle itself, as skills your agent gains: install, upgrade, remove, the interview, wrapping something you already built into a capability, and reviewing one. It also draws the line between **operating** and **building** mode — a chat message can seed a cron or a persona as easily as a one-off answer, so before your agent builds something durable it stops and offers to plan it properly. |
| [**kb**](capabilities/kb/) | Where your data lives. Say something worth keeping and it's filed — no form, no questions. Ask later and you get an answer *with sources*, or an honest "not in the KB". Several bases (personal, work) with rules deciding what lands where, and a deterministic `kb` tool other capabilities call. |

**Use-case — what it looks like when you build on them:**

| | |
|---|---|
| [**work-tracker**](capabilities/work-tracker/) | *"I need to write the CFP by Friday"* becomes a tracked commitment with time blocked for it, in the same exchange. A nightly steward finds what slipped and asks about it. Built entirely on kb — the reference example of one capability composing on another. |

Two properties that shape daily use:

- **Capture is fast; judgment is scheduled.** Filing a thought never blocks on a question. The
  passes that need thinking run overnight, where waiting is free.
- **Recall admits gaps.** Answers cite their sources, and "not in the KB" beats a confident
  invention.

## How this compares

Curated capability packs for agent harnesses already exist, and some are popular. The gap is
not *what* they ship — it's what happens when you adapt it.

|  | Personalize by | What an upgrade does |
|---|---|---|
| [gstack](https://github.com/garrytan/gstack) (~122k★) — dev-team skills, multi-host, paste-to-install | Forking the repo | You lose upstream. The community's own workaround is to stay forked; its harshest reviewer kept 6 of 35 commands |
| PAI / LifeOS — life-ops on Claude Code, 45 skills, has an interview | Forking the template | Same: no upstream story, single harness by construction |
| **aos** | Answering an interview, once | Re-applies your answers to the new version and shows you the diff |

The one-line version: **gstack's distribution architecture, applied to chief-of-staff work,
with the personalization layer it doesn't have.** An opinionated pack that assumes you are its
author sheds most of its surface on contact with anyone else; the fix isn't fewer opinions, it's
somewhere for yours to live that upgrades can't reach.

Researched properly, including the knowledge-base field (26 projects) and what was deliberately
*not* copied: [prior-art.md](https://github.com/AlmogBaku/aos/blob/spec/prior-art.md).

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

## One capability, any harness

![aos architecture: use-case capabilities compose on infrastructure capabilities, which break down into skills; your answers sit beside them in your own repo; the harness LLM combines the capability, your answers and a per-harness cheat-sheet into your own version, linked into your harness](docs/diagram.svg)

Only one thing is portable across harnesses today — the [Agent Skills](https://agentskills.io)
folder. Hooks, schedules, sub-agents and secret stores differ materially between them, so
cross-harness support is a **translation** problem, not a lowest-common-denominator one.

The translation is a **document, not code**: six sections teaching that harness's own LLM how the
concepts map onto its primitives. No adapter, no plugin, no glue — and with no document at all,
your agent works the mapping out itself. A capability declares what it needs from a host rather
than pretending the seam isn't there, and says honestly when a harness can't do something.

Anything that must be exact — computed names, hashes, layout — comes from a judgment-free tool:
files and exit codes, no LLM inside. Everything needing taste stays with the agent, behind the
diff gate.

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

More batteries are coming, and most of them are substrate — in
[build order](https://github.com/AlmogBaku/aos/blob/spec/ARCHITECTURE.md#7-reference-capabilities--build-order):

| Planned | Kind | What it unlocks |
|---|---|---|
| **agent-comms** | infra | Agents talking to each other: a real envelope, and a glass-box rule so there are no dark channels between them |
| **permission-gate** | infra | Capabilities that ship code, with per-user and per-group access control |
| **router** | infra | Front-door dispatch, so several personas stop fighting over one inbox |
| **ptt-mode** · **interviewing** | infra | Voice, and capabilities that interview on behalf of other capabilities |
| **news-tracker** | usecase | The deliberately boring port — proof the contract is cheap to build against |

## The loop this is all for

Someone builds a personal-trainer capability in their own harness. They ask their agent to wrap
it into a package; it splits the generic mechanism from their personal details. PR. You ask your
agent to install it, and the interview asks *you* — your goals, your gym days, your injuries. You
run your version. Their next release merges in without touching your answers.

**Wrap → share → install → personalize → upgrade.** Neither of you rewrote anything. Every
contract in this repo exists to make that loop work.

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
