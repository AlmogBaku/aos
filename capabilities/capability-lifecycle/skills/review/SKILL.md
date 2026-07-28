---
name: review
description: Reviews a capability as architecture and then as prose — traces its flows and decision points, maps its units against the resources powering them, diagrams it, stress-tests the logic, and checks that every command it documents exists and every artifact it writes has a reader. Use when asked to review, audit, critique or sanity-check a capability or its skills, before contributing one upstream, after building or evolving one, when something in a capability "looks wrong" but nobody can say where, or when a capability's prose and its tool may have drifted apart.
---

# capability-review

Not in context yet? Load the `capability-lifecycle` skill first — the map, the contract, and
the naming rules. This is the **read-only** counterpart to `capability-build`: it writes
nothing into any capability, and every finding is reported for a human to act on.

**A capability is software.** Its components are skills, agents, tools, crons and overlays;
its interfaces are prose an LLM follows; its bugs are unreachable branches, dangling edges
and unstated preconditions. Reviewing it sentence-by-sentence finds typos. Reviewing it as a
system finds the defects that matter — which is why Part 1 comes first and Part 2 is the
cheap sweep afterward, not the other way round.

Copy this checklist and work it in order:

```
- [ ] 1. Flows      — the journey, and every decision point
- [ ] 2. Components — units vs the resources powering them
- [ ] 3. Diagram    — if there is more than one moving part
- [ ] 4. Stress     — walk the tree adversarially
- [ ] 5. Journey    — happy path, failure modes, how each surfaces
- [ ] 6. Sweep      — commands, readers, claims, weaker models
- [ ] 7. Report     — findings, severity-ordered, with evidence
```

## 1. Flows and decision points **[A]**

Trace the journey end to end: where does input enter, what transforms it, where does it come
to rest. Then name the decision points — every place the SOP branches — **including the ones
the prose leaves implicit**. An unstated branch is where a weaker model improvises, and
improvisation in a capability is indistinguishable from a bug.

Read `CAPABILITY.md` for what is declared, then each skill for what actually happens. Where
they disagree, the skill wins at runtime and the manifest is the defect.

## 2. Components: units vs resources **[A]**

Two layers, kept separate, because conflating them hides both kinds of gap:

- **Business-logic units** — the jobs this capability does.
- **Resources** — what powers each job: a skill, an agent, a tool, a cron, a template, an
  overlay.

Then the edges: who invokes whom, who writes what, who owns which path. **A unit with no
resource is a wish; a resource with no unit is dead weight.** Both are findings.

Check the composition boundary too: a capability reaches another only through the shared
`main` agent or a tool on PATH — never a foreign skill (RFC-009 is open, so a cross-capability
skill reference is a defect today, not a style choice).

## 3. Diagram it **[A]**

Draw it when there is **more than one moving part** — several skills, or an agent, or a
schedule, or a tool. Skip it for a single-skill capability with nothing else: a two-box
diagram carries no information and teaches the reader that these diagrams are decoration,
which is exactly the write-only artifact check 6b exists to catch.

Mermaid, not ASCII — it is the kit's convention, renders on GitHub, and survives editing
where hand-aligned ASCII rots on the first change. Two shapes carry most capabilities: a
`sequenceDiagram` for the journey (who calls whom, in order) and a `flowchart` for the
component graph, resources in subgraphs. The kb capability's `docs/design.md` is the worked
example — `<home>/upstream/capabilities/kb/docs/design.md` in a household.

Drawing is the point, not decoration. A flow you cannot draw is a flow you do not understand
yet, and ambiguity that survives prose rarely survives a diagram.

Two rules, both learned the expensive way:

- A `;` inside a **sequence-diagram** message is a statement separator and breaks rendering —
  use an em dash. It is harmless inside a quoted flowchart label.
- **Verify by rendering, not by reading.** A block that parses in your head can still fail on
  GitHub, and a diagram that silently fails is worse than none: the reader sees raw source and
  stops trusting the document. Mermaid is not a repo dependency, so render with
  `npx @mermaid-js/mermaid-cli -i <file>` when you can. Offline, say the block is unverified
  rather than claiming it renders.

## 4. Stress the logic **[A]**

Walk the decision tree adversarially and look for:

- branches that cannot be reached, and branches that overlap so two paths both fire;
- two paths writing the same file, or the same state, with no ordering between them;
- an ordering assumption nobody declared ("after the nightly drain") — those rot silently
  when the other side changes;
- what happens on retry, on partial completion, and on a step that returns nothing.

Then check soundness against the kit's standing invariants: capture latency is sacred,
grants default to deny, a schedule has exactly one owner, and a capability that adds a second
lifetime rule beside `expires:` is wrong by construction.

## 5. Happy path, failure modes, journey **[A]**

For the main path and each failure mode, answer three things: what does success look like,
how does it fail, and **how would the failure surface** — as a crash a user reports, or as an
exit-0 wrong answer nobody notices. The second kind is the dangerous one, and it is what
sections 6a and 6c hunt.

Turn the interesting cases into eval queries where the capability's triggering is contested.
The kit's own `tests/evals/kb/` has near-miss sets to copy the shape from
(`<home>/upstream/tests/evals/kb/README.md`) — read its "harness could not measure" note before
trusting any number it produces.

## 6. The sweep **[D]** where a command can answer, **[A]** where judgment is needed

Cheap, mechanical, and it catches what every careful reading misses:

**a. Every command the prose names must exist, with those flags.** Run it, or read its
`--help`. The kit's linter validates schema — frontmatter, `used_by`, reference depth — and
cannot validate behaviour, so a verb that is really an option, a required flag omitted, or a
flag deleted from the tool all ship green. The failure lands on the agent that followed the
instruction. The kit ships `tools/check-kb-commands.mjs` for kb and work-tracker
(`node <home>/upstream/tools/check-kb-commands.mjs`); prefer running it to re-deriving it.

**b. Every artifact created must name its reader.** The rule the kit already states: *a queue
file is only justified when the work item has no artifact of its own*. Generalised — if
nothing reads what you write, delete the writer, not the reader. This is the single most
repeated defect in the kit's build-gap ledger (`<home>/upstream/docs/BUILD-GAPS.md`).

**c. Verify guardrail claims by reproduction, never by reading.** When prose says the tool
enforces, refuses, checks or scopes something, prove it on a throwaway fixture. Claims that a
tool protects you are worse than absent when false, because they stop the agent from
protecting itself.

**d. Would a weaker model reach the goal?** Unambiguous steps, no unstated prerequisites, an
explicit stop condition on every failure path, and the reasoning behind each rule so it
generalises past the literal case. For skill-authoring craft — description shape, triggering,
progressive disclosure — use `writing-skills` and `skill-creator` if installed; the aos naming
rules still win. Don't restate their guidance here.

**e. Prefer a script once a defect class appears twice.** Two careful readings that both miss
the same kind of thing is evidence a script is cheaper than a third reading.

## 7. Report **[A]**

Findings severity-ordered, each with the file, what breaks, and the evidence — a command you
ran, a reproduction, a dangling edge in the graph. Include the diagram if you drew one.

Two honesty rules. **Say when a pass found nothing**, rather than manufacturing findings to
justify the review — a clean architecture pass on a capability that has never been diagrammed
is a real result, but so is discovering the pass was too weak to find anything. And when a
finding is a judgment call rather than a defect, label it as one.

## Authority

- Freely: read every file, run read-only commands, build throwaway fixtures in `/tmp`, run
  `--help`, render diagrams.
- Report-only: every finding. This skill fixes nothing.
- Ask first: anything that would write into the capability under review, and any reproduction
  that touches real user data — fixtures go in `/tmp`, never a live base or profile.
