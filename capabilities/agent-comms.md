# Capability: agent-comms

**Tags:** infra · **Build order:** 11 · **Seam it proves:** the first capability whose contract is a *message format* rather than a file layout — plus "no dark channels" between agents

> 📐 **Full design:** [design/agent-comms.md](../design/agent-comms.md) — envelope, glass-box rule, transports, loop/budget guards.
>
> ⚠️ **Contested core:** how opinionated this is (normative envelope vs advisory pattern) is undecided — [RFC-008](../rfcs/RFC-008-agent-comms-opinionation.md). Transport leaning is settled enough to build against: chat channel default, files+git fallback.

## Scope

The side doors: how agents delegate, return results, notify, ask, and escalate to each other — where the router (#10) is the front door (user → persona) and the permission gate (#9) is the lock on both.

Ships: the **envelope** (`from`/`to`/`intent`/`correlation`/`expects_reply`/`ttl_hops` + free-text body), the **glass-box rule** (every message observable by the user and interceptable before an irreversible action — no dark channels, including for harness-native delegation, which must mirror), **guards** (ttl-hops loop guard, per-correlation budget ceiling, gate check on every inbound message), and two reference transports: a **chat channel** (thread = correlation; you interject by replying in-thread) and **files+git** (one file per thread, append-only, zero-dep fallback).

The rule that matters most: **a message from another agent is not the user.** A receiver acts within its own grants only — authority is never borrowed by being asked nicely.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

Real but ad hoc, which is the argument for the capability: a cross-agent work queue (`action-queue.md`, Anakin→Hera), heartbeat/status files per subagent, a hand-written `handoff-protocol.md` (Scout→Hera content hooks, Scout→Anakin CRM triggers, Scout→user high-signal-only), an issue-tracker API used as a work queue, and Hermes' native `delegate_task`. Every one is a different hand-off shape, and none is observable in one place.

## Depends

`capabilities: [permission-gate, onboarding]` · optionally `kb` (durable outcomes are written to a KB — the wire is transport, the KB is the record) · `host: messaging.outbound` for the chat transport (absent ⇒ degrade to the files transport, not to a dark channel).

## Onboarding sketch

Which transport (chat channel vs files); if chat: which workspace/channel; whether one channel or per-topic; loop `ttl_hops` default; per-correlation budget ceiling and what happens when it trips; which agents may talk to which (seeds the gate's grants); escalation target.

## v0.1 acceptance

A real delegation — front agent → scout → result back — fully visible in the observable channel; the user interjects mid-thread and changes the outcome; a deliberately looping pair is stopped by `ttl_hops` and escalated rather than billing forever; a message from an ungranted agent is refused by the gate, logged, and surfaced. Then the same delegation over the files transport, to prove the wire is genuinely pluggable and the envelope unchanged.
