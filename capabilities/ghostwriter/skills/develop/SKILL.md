---
name: develop
description: Use when an abstract is selected, a user wants to start a named content idea, or an in-development Blog, LinkedIn, or X piece needs its narrative or draft advanced. Do NOT use to propose new abstracts (that is ghostwriter-ingest) or to review a finished draft for grounding, sensitivity, and voice (ghostwriter-critique).
---

# Develop Content

1. Run {{skill: ghostwriter}}'s backlog preflight before any state change. Normally, nonzero stops. The sole exception is one `source_idea_id` duplicate-transfer finding for the same queued idea and piece: acquire the workspace lock, inspect both artifacts, finish archiving the verified source idea when the piece is complete, otherwise move only the incomplete piece through the harness's recoverable trash mechanism; rerun preflight and stop on any remaining finding. Check the active-piece limit before normal development.
2. If the user cannot answer a format, narrative, or channel choice from lived experience, show two short alternative shapes to react to. Do not keep rephrasing the same abstract question.
3. For a queued idea, persist its ID as `source_idea_id`, create and verify an unused `pieces/<slug>/piece.md` at `stage: angles`, then mark the idea `selected` and archive it. For `let's write <topic>`, first create one queued idea using {{skill: ingest}}.
4. Retrieve only the evidence needed for this piece.
5. Create a lean brief before prose: specific reader, goal, promise, anchor channel from `{{mod: content_channels}}`, structural shape, and earned length. Stop and surface an unsupported channel. Preserve the idea's Evidence map in the piece and extend it claim-by-claim; infer only what the sources support. Ask one question when a missing choice materially changes the piece.
6. Develop in gated steps — **one step, then stop for the user**. Never pass a stage whose decision is not recorded, and never write more than one section in a step.
   - `angles`: three cards under `## Angles` — hook, three-sentence synopsis, shape, and the Evidence-map claims each rests on. Ask which to take: pick one, merge, or redirect.
   - `outline`: record the chosen angle under `## Abstract`, set `stage: outline`, and write the beats under `## Outline` with evidence per beat (hook → lived scene/problem → mechanism → proof → implication; for long-form, choose a structural archetype deliberately and cut any beat that carries no argumentative weight). Ask what to change.
   - `draft`: once the outline is approved, set `stage: draft` and write **one section** under `## Current draft` using `reference/writing-guide.md`, updating `Sections done`. Ask for a reaction before the next section.
7. Before each stop, write the exact question under `## Next action`, set `status: waiting` and `next_action: user-decision`; after the answer, record it, restore `status: developing` and `next_action: develop`. Ask only what materially unlocks the story, and explain tradeoffs before any choice UI.
8. In an unattended run nobody answers: never ask; leave a piece that waits on a decision untouched; give a piece whose decision is recorded exactly its next step, then stop at that step's question.
9. When every section is written and the user approves the whole, set `next_action: critique`. Do not publish.

Short insights may stay short. Never inflate an observation into long-form to satisfy a format.
