---
name: develop
description: Use when an abstract is selected, a user wants to start a named content idea, or an in-development Blog, LinkedIn, or X piece needs its narrative or draft advanced. Do NOT use to propose new abstracts (that is ghostwriter-ingest) or to review a finished draft for grounding, sensitivity, and voice (ghostwriter-critique).
---

# Develop Content

1. Run {{skill: ghostwriter}}'s backlog preflight before any state change. Normally, nonzero stops. The sole exception is one `source_idea_id` duplicate-transfer finding for the same queued idea and piece: acquire the workspace lock, inspect both artifacts, finish archiving the verified source idea when the piece is complete, otherwise move only the incomplete piece through the harness's recoverable trash mechanism; rerun preflight and stop on any remaining finding. Check the active-piece limit before normal development.
2. If the user cannot answer a format, narrative, or channel choice from lived experience, show two short alternative shapes to react to. Do not keep rephrasing the same abstract question.
3. For a queued idea, persist its ID as `source_idea_id`, create and verify an unused `pieces/<slug>/piece.md`, then mark the idea `selected` and archive it. For `let's write <topic>`, first create one queued idea using {{skill: ingest}}.
4. Retrieve only the evidence needed for this piece.
5. Create a lean brief before prose: specific reader, goal, promise, anchor channel from `{{mod: content_channels}}`, structural shape, and earned length. Stop and surface an unsupported channel. Preserve the idea's Evidence map in the piece and extend it claim-by-claim; infer only what the sources support. Ask one question when a missing choice materially changes the piece.
6. Ask only questions that materially unlock the story. Before asking, write the exact question under `## Next action`, set `status: waiting` and `next_action: user-decision`; after the answer, restore `status: developing` and `next_action: develop`. If a choice is needed, explain tradeoffs before the choice UI.
7. Shape: hook → lived scene/problem → mechanism → proof → implication. For long-form, choose a structural archetype deliberately and cut any section that does not carry argumentative weight.
8. Draft for the selected anchor channel using `reference/writing-guide.md`.
9. Set `next_action: critique`. Do not publish.

Short insights may stay short. Never inflate an observation into long-form to satisfy a format.
