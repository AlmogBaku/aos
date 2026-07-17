# RFC-007: Permission-gate policy vocabulary

**Status:** open · **Decides:** the policy format the permission-gate capability standardizes · **Capability:** [permission-gate](../capabilities/permission-gate.md) (contested core; extraction plan unaffected)

## Question

Many of us have independently built or patched a gate. The known reference (the Hermes WhatsApp gate) supports: a group open to *everyone but only for a specific task*; a group restricted to *specific users*; *blocked by default*; unknown senders parked in a pending/review state. Other members' gates have semantics we haven't inventoried yet. What single policy vocabulary do we standardize so one capability replaces all of them — without losing anyone's semantics?

## Constraint

Whatever the vocabulary is, it must express the §4.3 model (subjects × objects × verbs) so the gate and KB routing share one ACL language, and it must survive the enforcement being per-harness code (hook or patch, §2.4) while the *policy* stays harness-neutral in the capability.

## Options

1. **Typed rules file (YAML):** precise, lintable, enforceable by dumb code. Risk: real policies have judgment in them ("family group: anything reasonable, but never business") that rules can't express.
2. **Markdown policy + LLM interpretation:** maximally expressive, matches how people actually describe their boundaries. Risk: the enforcement point is exactly where you don't want stochastic behavior.
3. **Hybrid (likely):** typed rules for the hard skeleton (who, which group, default posture) + an optional prose clause per rule that the agent consults for task-scope judgment — deterministic deny/allow first, judgment only inside an already-allowed lane.

## How to decide

Inventory before argument: each member documents their existing gate's semantics (an importer-style wrap of the policy, not the code). The vocabulary is whatever expresses the union — anything none of the existing gates needs stays out (rule-of-two).

## Process

Inventory phase first (no deadline until ≥3 gates are documented); then options + auto-accept per RFC-003.
