# RFC-008: How opinionated is agent-to-agent communication?

**Status:** open · **Decides:** whether the agent-comms envelope + glass-box rule are normative · **Capability:** [agent-comms](../capabilities/agent-comms.md) · **Design:** [design/agent-comms.md](../design/agent-comms.md)

## Question

Once a user runs several agents, they delegate, hand back results, notify, and escalate to each other. The design proposal splits this into two layers: an **envelope** (from/to/intent/correlation/ttl + a glass-box rule) and a **wire** (the transport). The transport question has a working answer (below). What's undecided is **how firm the first layer is** — and that choice determines whether "agent traffic is observable" is a property of the kit or merely a suggestion.

## Options

1. **Opinionated envelope + pluggable wire.** The envelope and the glass-box rule (*every A2A message must be observable by the user and interceptable before an irreversible action*) are **normative**: a capability that talks to another agent must use them, and CI/lint can check it. Transport stays pluggable behind a cheat-sheet, one default shipped. Pro: observability and gate-integration become guarantees the whole composing set can rely on; the "no dark channels" rule is enforceable. Con: a real constraint on every future capability author, including for trivial in-harness hand-offs.
2. **Fully opinionated — one transport, mandated.** Pick the wire too (chat), and everyone uses it. Pro: one code path, easy to test, richest observability everywhere. Con: hard dependency on a third-party vendor in a commons project; excludes anyone without it; violates the kit's own "works on the harness you already run" instinct.
3. **Unopinionated — a transport-neutral contract only.** Publish the envelope as a *recommended* pattern with no shipped default and no observability requirement. Pro: maximum freedom, zero constraint on contributors. Con: forfeits the entire benefit — agent traffic goes back to being invisible and each capability re-invents hand-offs, which is the status quo this capability exists to replace.

## Transport (the part with a working answer)

**Chat channel by default, files+git as the zero-dep fallback**, with harness-native delegation allowed as a fast path *only if it mirrors to the observable channel*. Google's **A2A protocol is deferred** — it solves cross-vendor interop, needs a server per agent, and offers no intervention affordance; the envelope is drawn to map onto it later if someone needs to talk to an agent they don't own. This part is not what the RFC is asking about, but reviewers should push back here too if they disagree.

## Recommendation

**Option 1**, with the glass-box rule stated as the single normative sentence and the envelope kept minimal (rule-of-two). Reasoning: the reason to build this capability at all is that agent-to-agent failures are *invisible* — loops, misdelegations, an agent treating another agent as the user. Option 3 keeps the failure mode; option 2 buys enforcement at the price of a vendor lock the project's ethos rejects. Option 1 is the only one that makes observability a property rather than a hope, while still letting a user run the whole thing on nothing but files.

Note that this mirrors a decision the kit already made once: the KB layer is opinionated about *the model and the safety rule* and pluggable about *the substrate*. Same shape, same reasons.

## How to decide

Cheap evidence beats argument: wire up one real delegation (front agent → a research/scout agent → result back) over the chat transport, and the same one over files. Compare — how quickly did you notice a wrong hand-off, and could you actually interject? Then decide whether that property is worth making mandatory.

## Process

Auto-accept per RFC-003 window. Blocking requires a counter-proposal, not a preference.
