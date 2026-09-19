---
name: critique
description: Use when reviewing a content draft for source support, privacy, sensitive disclosure, authentic voice, factual accuracy, or residual AI-shaped prose before manual publication. Do NOT use to advance a draft that is still being written (that is ghostwriter-develop) or to cut channel variants from an approved anchor (ghostwriter-repurpose).
---

# Critique Content

Before mutation, run {{skill: ghostwriter}}'s preflight, acquire its workspace lock, rerun preflight, and always release the lock.

Review in this order:

1. **Brief adherence:** does the draft serve the stated reader, goal, promise, channel, structure, and earned length? Halt early if not.
2. **Grounding:** validate `## Evidence map`: map each first-person claim, fact, example, and number to its source path plus turn or line range. Unsupported claims remain visible and block approval.
3. **Sensitivity:** flag investor/deal details, customer identity, secrets, non-public IP/plans, internal numbers, and identifiable private anecdotes. Anonymization is a proposal, never automatic clearance. Any uncleared private-source use sets `approval_required: true`, keeps `status: review`, and routes to `user-decision`.
4. **Structure and substance:** hook earns the read; every section carries argumentative weight; the closing lands intentionally; cut padding instead of adding more words.
5. **Voice:** compare with `{{mod: voice_examples_path}}` when configured; each example must state its approval and source. If no approved corpus exists, preserve the user's supplied vocabulary and do not invent a voice verdict. Do not make it “professional” by sanding off the point.
6. **Writing:** use `reference/humanization.md` once, after substance is locked. Change only detected problems.

The user owns what publishes, voice, factual positions, and sensitive-source clearance. AI accelerates retrieval, draft options, and flagging; it does not clear a piece.

Write concise blockers and the requested decision under `## Next action`. While blocked, use `status: review`, `next_action: user-decision`, and `approval_required: true`. On explicit clearance, atomically remove only resolved sensitive flags, change only approved Evidence-map entries from `review` to `none`, set `private_source_clearance: true` and `approval_required: false`, then route to `manual-approval`. Only final approval moves to `approved-manual-publish` with `manual-publish` or requested `repurpose`.
