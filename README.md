<div align="center">

# aos

*The batteries for your agent harness.*

[![CI](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml/badge.svg)](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![Spec](https://img.shields.io/badge/spec-ARCHITECTURE%20v0.1-001F5C.svg?style=flat-square)](https://github.com/AlmogBaku/aos/tree/spec)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)

[Install](#install) • [What's included](#whats-included) • [The capability](#the-capability) • [Harnesses](#harnesses) • [Docs](#docs)

</div>

**A kit for building your own personal assistant.**

Your harness — Hermes, OpenClaw, NanoClaw, Claude Code — is a runtime: an agent, a model, tools,
somewhere to put a cron. It is not an assistant. Everything above the runtime you build yourself,
from scratch, per harness, and it lands as loose files you can't package, share, or move.

This kit is that missing layer, in two halves:

| | |
|---|---|
| **The protocol** | How you package anything for a runtime: the **capability**, an interview that personalizes it, an overlay that survives upgrades, a translation per harness. No runtime, no daemon, no service — the new software is a prompt. |
| **The implementations** | The batteries: **infrastructure** capabilities everything else builds on (a knowledge base, the capability lifecycle, soon agents talking to each other) and **personal-assistant** capabilities built on those. |

A personal chief of staff shouldn't be anyone's proprietary IP, so this is a commons — built for
ourselves, on whatever harness we each run.

## Install

Paste this to your agent:

> Clone https://github.com/AlmogBaku/aos.git to ~/aos/upstream, read
> ~/aos/upstream/BOOTSTRAP.md, then set me up.

That's the whole funnel. Your own agent does the work: it interviews you (identity, timezone,
sacred hours, red lines), writes your answers somewhere it will never overwrite, wires the skills
into your harness, and records every artifact so removal is exact.

Prerequisites: `git`, [`uv`](https://docs.astral.sh/uv/), and an agent harness. What actually
happens: [docs/INSTALL.md](docs/INSTALL.md).

> [!IMPORTANT]
> Every change is diff-previewed before it touches your harness, and everything installed is
> recorded — removal walks that record backwards. The diff is a standing safety net, deliberately
> not a consent prompt per write. Separately and absolutely: your agent never pushes, forks, opens
> a PR or files an issue without you asking it to.

> [!TIP]
> **Reading this as an agent?** Clone first, then follow the *local* copy at
> `~/aos/upstream/BOOTSTRAP.md` — it reads files out of the clone, so working from this web page
> strands you two steps in.

## What's included

**Infrastructure — the substrate everything else builds on:**

| | |
|---|---|
| [**capability-lifecycle**](capabilities/capability-lifecycle/) | The lifecycle as skills your agent gains: install, upgrade, remove, the interview, wrapping something you already built into a capability, reviewing one. It also draws the line between **operating** and **building** mode, so before your agent makes something durable it stops and offers to plan it properly. |
| [**kb**](capabilities/kb/) | Where your data lives. Say something worth keeping and it's filed — no form, no questions. Ask later and you get an answer *with sources*, or an honest "not in the KB". Several bases (personal, work), rules deciding what lands where, and a deterministic `kb` tool other capabilities call. |

**Personal-assistant capabilities, built on those:**

| | |
|---|---|
| [**work-tracker**](capabilities/work-tracker/) | *"I need to write the CFP by Friday"* becomes a tracked commitment with time blocked for it, in the same exchange. A nightly steward finds what slipped and asks about it. |

Coming next, mostly more substrate: **agent-comms** (agents talking to each other, with no dark
channels), **permission-gate**, **router**, **ptt-mode** and **interviewing** (voice),
**news-tracker**.

## The capability

The protocol has one noun. A **capability** is an installable package — **think a distro package,
apt for your agent** — of five building blocks:

| Block | What it is |
|---|---|
| **Skills** | knowledge your agent loads on demand — portable [Agent Skills](https://agentskills.io) folders |
| **Agents** | personas that run scheduled or delegated work |
| **Tools** | real commands on PATH, no LLM inside. Also how one capability reaches another: a process boundary, not a shared prompt |
| **Schedules** | crons, agent-driven or script-direct |
| **Patches** | harness modifications, where genuinely unavoidable |

Installing one is a **conversation, not a command**. `install`, `update` and `remove` are things
you say; your harness's own LLM does the work, and the only thing a tool ever touches is
bookkeeping, hashes and diffs.

**And the shipped capability is not the installed one.** Upstream ships a template; your harness
runs *your* version. The interview asks how you want it to behave, your answers go in a repo you
own, and the install stays reconstructible as `template × your answers`:

- Upstream never ships, writes or merges your answers. `git pull` cannot reach them.
- An upgrade re-runs the transform against the new version. **That transform is judgment, not
  templating** — which is why the gate is a git diff in your own repo: read what changed, commit
  to accept, `git revert` to roll back.
- Edit the installed thing by hand and your agent folds the change back into your answers.

Two kinds, and the manifest says which. **Infrastructure** (`tags: [infra]`) is substrate others
layer on; **use-case** (`tags: [usecase]`) solves one problem by composing the layers below. That
layering is the point: `work-tracker` is under 900 lines of markdown and YAML with no storage
engine, no retrieval and no installer of its own, because the two infra capabilities beneath it
have those. Its steward calls `kb find --where status=next` as a shell command.

Where this sits next to curated packs like gstack, and the 26-project survey behind `kb`:
[prior-art.md](https://github.com/AlmogBaku/aos/blob/spec/prior-art.md).

## Harnesses

![aos architecture: use-case capabilities compose on infrastructure capabilities, which break down into skills; your answers sit beside them in your own repo; the harness LLM combines the capability, your answers and a per-harness cheat-sheet into your own version, linked into your harness](docs/diagram.svg)

Only the [Agent Skills](https://agentskills.io) folder is portable today; hooks, schedules,
sub-agents and secret stores differ materially. So support is a **translation** problem, and the
translation is a **document, not code** — six sections teaching that harness's own LLM how the
concepts map onto its primitives. No adapter, no plugin, and with no document at all your agent
works the mapping out itself.

**Written for five harnesses, verified end to end on one.** A capability lists a harness only once
someone has actually run it there, which is why exactly one row below is bold.

| Harness | Status |
|---|---|
| [Hermes](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-hermes.md) | **Supported** — verified by a real install, not a simulation |
| [OpenClaw](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-openclaw.md) · [NanoClaw](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-nanoclaw.md) · [Nanobot](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-nanobot.md) · [Claude Code](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-claude-code.md) | Translation written from the harness's docs; no real install has run against it yet |
| OpenCode | Planned — and the no-document path works today |

[Adding one](CONTRIBUTING.md) is one document.

## The loop this is all for

Someone builds a personal-trainer capability in their own harness and asks their agent to wrap it
into a package; it splits the generic mechanism from their personal details. PR. You install it,
and the interview asks *you* — your goals, your gym days, your injuries. Their next release merges
in without touching your answers.

**Wrap → share → install → personalize → upgrade.** Neither of you rewrote anything. Every
contract in this repo exists to make that loop work, and the first step is the cheapest
contribution path there is: you already have a working version of something.

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
