<div align="center">

# aos

[![CI](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml/badge.svg)](https://github.com/AlmogBaku/aos/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Spec](https://img.shields.io/badge/spec-ARCHITECTURE%20v0.1-001F5C.svg)](https://github.com/AlmogBaku/aos/tree/spec)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

> Memory and follow-through for the AI agent you already run.

Your agent holds a conversation well. It doesn't remember what you told it last week, doesn't
track what you said you'd do, and does nothing while you sleep. **aos** adds those — as
markdown your agent installs into itself. No runtime, no daemon, no service to sign up for.

![aos architecture](docs/diagram.svg)

> [!NOTE]
> `aos` is a placeholder name — [RFC-001](https://github.com/AlmogBaku/aos/blob/spec/rfcs/RFC-001-naming.md) picks the real one.

## Install

Prerequisites: `git` and [`uv`](https://docs.astral.sh/uv/). Then paste this to your agent:

> Clone https://github.com/AlmogBaku/aos.git to ~/aos/upstream, read
> ~/aos/upstream/BOOTSTRAP.md, then set me up.

It does the rest — a five-minute interview (timezone, working hours, what's sacred, your red
lines), then it wires the skills into itself.

> [!IMPORTANT]
> Nothing is written without your approval. You see the full diff of every change first, and
> every file it creates is recorded, so removal is exact.

Afterwards, in your own words:

```text
"the Berlin office moved to Torstraße"        → filed, no questions asked
"I need to write the CFP by Friday"           → tracked, with time blocked for it
"what do I know about the Berlin trip?"       → answered, with sources
```

Under those sit real commands you can run yourself:

```bash
kb capture --text "the Berlin office moved to Torstraße"   # never blocks on a question
kb find --where status=next                                # query the metadata, not the prose
```

## What you get

| Capability | What it does |
|---|---|
| [**kb**](capabilities/kb/) | Files what you say without asking questions, and answers questions later with sources — or an honest *"not in the KB"*. Separate bases for personal and work, with rules deciding what lands where. |
| [**work-tracker**](capabilities/work-tracker/) | Turns *"I need to write the CFP by Friday"* into a tracked commitment with time blocked for it, in the same exchange. A nightly pass finds what slipped and asks about it. |
| [**capability-lifecycle**](capabilities/capability-lifecycle/) | Installs, upgrades and removes the above — and wraps something you already built into a capability others can install. |

**Your answers survive upgrades.** The interview writes them into *your* repo, which upstream
never ships and never merges — so `git pull` cannot touch them. An upgrade re-applies your
answers to the new version and shows you the diff; undoing one is `git revert`.

## Supported harnesses

| Harness | Status |
|---|---|
| [Hermes](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-hermes.md) | **Supported** — installed end to end, for real, as CI's third tier |
| [OpenClaw](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-openclaw.md) · [NanoClaw](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-nanoclaw.md) · [Nanobot](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-nanobot.md) · [Claude Code](capabilities/capability-lifecycle/skills/capability-lifecycle/reference/harness-claude-code.md) | Cheat-sheet shipped, research-drafted — not yet proven by a real install |
| OpenCode | Planned — installs today without a cheat-sheet; [contribute one](CONTRIBUTING.md) |

**Adding a harness means writing a document, not code:** six sections teaching that harness's
own LLM how aos concepts map onto its primitives. No adapter, no plugin, no glue. Without one,
your agent works the mapping out itself.

## How it works

A capability is a directory of skills, agent specs and schedules. Installing one is a
conversation rather than a command: your agent reads the capability, applies your answers,
writes the result into your own repo, and links it into itself.

Anything that must be exact — computed names, hashes, file layout — is done by a small
judgment-free tool with no LLM inside: files and exit codes only. Everything needing taste
stays with the agent, behind the diff gate.

Longer tour in plain words: [docs/CONCEPTS.md](docs/CONCEPTS.md).

## Why this exists

A chief of staff shouldn't live inside a company's proprietary IP. The harness vendors — and a
wave of startups on top of them — are commercializing exactly this layer. We build it anyway,
for ourselves, on whatever harness we each run, and we're not paying rent on our own work.
MIT, one repo, belonging to the people who build with it.

The loop every contract here exists to serve: someone builds a personal-trainer capability in
their own harness → asks their agent to wrap it → PR → you install it → the interview asks
*you* (your goals, your gym days, your injuries) → you run *your* version → their next release
merges in without touching your answers.

## Docs

| Doc | The question it answers |
|---|---|
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | What is a capability, an overlay, a base? |
| [docs/INSTALL.md](docs/INSTALL.md) | What actually happens when I install this? |
| [docs/USAGE.md](docs/USAGE.md) | How do I use it day to day? |
| [docs/TESTING.md](docs/TESTING.md) | How is any of this tested without a runtime? |
| [docs/BUILD-GAPS.md](docs/BUILD-GAPS.md) | Where has building diverged from the spec? |
| [BOOTSTRAP.md](BOOTSTRAP.md) | *(for your agent)* the exact install sequence |
| [`spec` branch](https://github.com/AlmogBaku/aos/tree/spec) | The normative contracts, RFCs and design deep-dives |

Coming next, each proving one new seam: voice (**ptt-mode**), capability-on-capability
(**interviewing**), **news-tracker**, capabilities that ship code (**permission-gate**),
front-door dispatch (**router**), agent↔agent (**agent-comms**).
