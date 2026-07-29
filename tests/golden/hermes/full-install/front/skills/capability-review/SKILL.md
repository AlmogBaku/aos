---
name: capability-review
description: 'Reviews a capability as architecture and then as prose — traces its
  flows and decision points, maps its units against the resources powering them, diagrams
  it, stress-tests the logic, and checks that every command it documents exists and
  every artifact it writes has a reader. Use when asked to review, audit, critique
  or sanity-check a capability or its skills, before contributing one upstream, after
  building or evolving one, when something in a capability "looks wrong" but nobody
  can say where, or when a capability''s prose and its tool may have drifted apart.
  Read-only, so it reports findings and fixes nothing: Do NOT use to apply a fix —
  that is capability-contribute upstream, or capability-evolve for one user.'
metadata:
  aos:
    origin: capability-lifecycle@0.3.4
---
# capability-review

Not in context yet? Load the `capability-lifecycle` skill first — the map, the contract, and
the naming rules. **Read-only** counterpart to `capability-build`: writes nothing, reports
everything for a human to act on.

**A capability is software.** Its components are skills, agents, tools, crons and overlays; its
interfaces are prose an LLM follows; its bugs are unreachable branches, dangling edges and
unstated preconditions.

Reviewing it sentence-by-sentence finds typos. Reviewing it as a *system* finds the defects that
matter — **which is why steps 1–5 come first and the textual sweep comes last, not the other way
round.** Two real runs of this skill on this kit each found every high-severity defect in steps
1–5 and none in the sweep, and one of those was a data-loss bug that two careful readings had
already missed. If the cheap mechanical checks feel more productive to start with, that is the
temptation this order exists to defeat.

Section headings carry **[A]** where the work is judgment and **[D]** where a command answers.
The [D] parts cannot be faked; do those literally rather than concluding them.

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

**A shipped tool's source is in scope**, not just its `--help`. Prose can only promise; the code
is what happens. Reviews of this kit have found their worst defects — data loss, a silently
flipped record — by reading the tool, never by reading about it.

## 2. Components: units vs resources **[A]**

Two layers, kept separate — conflating them hides both kinds of gap:

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
schedule, or a tool. Skip it for a single-skill capability with nothing else: a two-box diagram
carries no information, and shipping one teaches the reader that these diagrams are decoration —
the write-only artifact 6b exists to catch. The judgment is whether *relationships* matter here,
not how many files there are.

Mermaid, not ASCII — it is the kit's convention, renders on GitHub, and survives editing
where hand-aligned ASCII rots on the first change. Two shapes carry most capabilities: a
`sequenceDiagram` for the journey (who calls whom, in order) and a `flowchart` for the
component graph, resources in subgraphs.

**Derive the graph from the skills and the tool first, then diff it against any diagram the
capability already ships — a mismatch is a finding, and the shipped one is usually the stale
side.** Reading an existing diagram first tells you what someone believed, which is exactly what
you are testing. For shape only (not content), `<home>/upstream/capabilities/kb/docs/design.md`
is a worked example.

Drawing is the point, not decoration: a flow you cannot draw is a flow you do not understand yet,
and ambiguity that survives prose rarely survives a diagram. The data-loss bug mentioned above
was found exactly here — two instructions that read as unrelated sentences named one directory,
which is invisible in prose and unmissable as two nodes.

Two rules, both learned the expensive way:

- A `;` inside a **sequence-diagram** message is a statement separator and breaks rendering —
  use an em dash. It is harmless inside a quoted flowchart label.
- **Verify by rendering, not by reading.** A block that parses in your head can still fail on
  GitHub, and a diagram that silently fails is worse than none: the reader sees raw source and
  stops trusting the document. Three rungs, best first: `npx @mermaid-js/mermaid-cli -i <file>`
  renders for real, but needs a Puppeteer browser and fails in most sandboxes and CI containers;
  failing that, `mermaid@11`'s `parse()` under a jsdom global validates the grammar (including
  the `;` case) with no browser; failing both, say **unverified** rather than implying it
  renders. Name which rung you used — "grammar-verified, not render-verified" is an honest
  result, "renders correctly" on an unrendered block is not.

## 4. Stress the logic **[A]**

Walk the decision tree adversarially and look for:

- branches that cannot be reached, and branches that overlap so two paths both fire;
- two paths writing the same file, or the same state, with no ordering between them;
- an ordering assumption nobody declared ("after the nightly steward pass") — those rot silently
  when the other side changes;
- what happens on retry, on partial completion, and on a step that returns nothing.

Then check soundness against whichever standing invariants this capability actually touches —
skip the rest rather than padding: capture latency is sacred, grants default to deny, a schedule
has exactly one owner, one lifetime rule (`expires:`) and no second, and **attribution is the
enforcement substrate** — every write is its own commit with the human as author and the acting
agent as committer, so anything that lets a write reach git unattributed, or under the wrong
subject, breaks the audit that everything else rests on.

## 5. Happy path, failure modes, journey **[A]**

For the main path and each failure mode, answer three things: what does success look like,
how does it fail, and **how would the failure surface** — as a crash a user reports, or as an
exit-0 wrong answer nobody notices. The second kind is the dangerous one, and it is what
sections 6a and 6c hunt.

Where — and only where — the capability's *triggering* is genuinely contested, propose eval
queries in your report; **you write no files, so do not create them.** `tests/evals/kb/` shows
the near-miss shape, and its "harness could not measure" note is required reading before anyone
trusts a number from that harness. If triggering is not contested, say so and move on.

## 6. The sweep **[D]** where a command can answer, **[A]** where judgment is needed

Mechanical, and it catches what careful reading misses. **This is the step to parallelise** — 6a
and 6c are per-claim and independent, and 6c's reproductions are the slowest thing in the review,
so hand them to subagents and collect the verdicts.

**Do not parallelise steps 1–5, and do not split a capability by skill.** Every defect worth
finding in this kit lived *between* skills, not inside one: of ten real findings in one review,
nine needed two or more skills in view at once and exactly one was visible in a single file. An
agent holding only `upgrade` cannot see that its render destination is another skill's source
directory — that finding *is* the relationship. The economics point the same way: the shared
context every per-skill agent must re-read (manifest, entry skill, contract, naming) outweighs
the per-skill bodies it would save, so splitting by skill multiplies context instead of saving it.
Fan out **by capability** when reviewing several; keep one capability in one head.

**a. Every command the prose names must exist, with those flags.** Run it, or read its
`--help`. The kit's linter validates schema — frontmatter, `used_by`, reference depth — and
cannot validate behaviour, so a verb that is really an option, a required flag omitted, or a
flag deleted from the tool all ship green. The failure lands on the agent that followed the
instruction.

The kit ships `tools/check-kb-commands.mjs`, but it is **hardcoded to kb and work-tracker** — run
it only when one of those is your target. On anything else it exits 0 without opening the
capability under review, which reads as a pass and is not one. Otherwise extract the invocations
yourself and diff them against `--help`. And note what no such script can see: a command can
exist with exactly the documented flags and still be unable to do what the prose claims.

**b. Every artifact created must name its reader.** The rule the kit already states: *a queue
file is only justified when the work item has no artifact of its own*. Generalised — if
nothing reads what you write, delete the writer, not the reader. This is the single most
repeated defect in the kit's build-gap ledger (`<home>/upstream/docs/BUILD-GAPS.md`).

**c. Verify guardrail claims by reproduction, never by reading.** When prose says the tool
enforces, refuses, checks or scopes something, prove it on a throwaway fixture. Claims that a
tool protects you are worse than absent when false, because they stop the agent from
protecting itself.

**d. Would a weaker model reach the goal? [D] where you can prove it.** Don't conclude this —
test it. Take the two longest branches you drew in step 1 and name, concretely, the one fact a
fresh agent would lack at each: an unstated prerequisite, a missing stop condition, a required
flag the prose omits. If you cannot name one, say the branch is clean. Then check the aos-side
mechanics: every skill declared in `used_by`, installed names computed not authored, and the
manifest's own counts matching the README and its prose — a version-bumping commit is exactly
where those drift.

For skill quality itself, work [reference/skill-rubric.md](reference/skill-rubric.md): eight
judgment dimensions — four for the body, four for the description — with the mechanical half
excluded because the linter already fails the build over it. **Read its opening rule before
scoring anything.** The rubric is a floor: a weak dimension means something is wrong, a strong
one means stop. Polishing a skill that already reads well buys the last points by deleting
reasoning, and reasoning is what lets a model handle the case a rule does not literally name.
Task achievement is the target, not a tidy score.

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
