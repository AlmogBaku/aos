# Capability: permission-gate

**Tags:** infra · **Build order:** 9 · **Seam it proves:** capabilities-ship-code — `adapters/*/plugins/`, hook-vs-patch, the §4.3 ACL model enforced

> ⚠️ **Contested core:** the policy vocabulary is under active decision in [RFC-007](../rfcs/RFC-007-permission-gate-vocabulary.md) — inventory of the group's existing gates comes first. The extraction plan below is unaffected.

## Scope

Access control over inbound traffic to the agent — per-channel/group, per-user, per-task. The policy vocabulary is the §4.3 model (subjects × objects × verbs), expressed as user-editable rules; enforcement is harness-native code. Live reference semantics (from the existing Hermes WhatsApp gate): a group can be open to everyone **but only for a specific task**; a group can be restricted to specific users; default is blocked; unknown senders land in a pending/review state rather than reaching the agent.

This is the reference proof that **capabilities can ship software — as standalone programs**: the gate itself is one encapsulated program (whatever language its author wrote it in), invoked across a process boundary; the per-harness part is only a thin shim — a hook that calls the program (where a hook/middleware surface exists) or a **maintained patch with a standing upstream-PR obligation** (where it doesn't), declared in the adapter dir so `doctor` can watch for harness-version drift (ARCHITECTURE §2.4). A Python gate serving a TypeScript harness is the intended demonstration, not an edge case.

## What exists today (extraction sources — in Almog's live setup, the first wrap target)

- The live Hermes WhatsApp gate (user modes: principal / approved_external / pending / blocked / unknown; driven by `state/USERS.md` → `sync_users.py` → `users.json`). Note from the infra inventory: the operating manual references `gateway/permission_gate.py` but the file wasn't found in `~/.hermes` — locate the actual implementation (likely inside the Hermes package) before extraction.
- Multiple collaborators report having patched or built equivalents on their harnesses — the import candidates that will define the neutral policy format.

## Depends

`capabilities: [onboarding]` · `host:` nothing from the standard vocabulary — this capability *is* the test of the non-standard surface: each adapter declares `hook` / `patched` / `unsupported` in the support matrix.

## Onboarding sketch

Channels/groups inventory, default posture (block-all recommended), per-group rules (who + optionally task-scope), pending-review flow (where do unknown-sender requests surface), escalation contact.

## v0.1 acceptance

The Hermes gate extracted and reinstalled through the framework with identical behavior; one second harness marked honestly (`hook`, `patched`, or `unsupported`); a task-scoped group rule enforced end-to-end (allowed task passes, anything else refused).
