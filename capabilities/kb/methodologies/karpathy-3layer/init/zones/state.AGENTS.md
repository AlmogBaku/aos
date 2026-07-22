# AGENTS — state/ (Layer 3)

High-churn current truth. **Rewritten, not appended** (except LEARNINGS.md). Never an
archive; git history is the archive — **no `.backup.*` files, ever** (lint flags them).

| file | discipline | budget |
|---|---|---|
| `STATE.md` | live snapshot; rewrite freely, keep it a *snapshot* — status narratives and checkpoints belong in the writing agent's own workspace, not here | 8K chars |
| `PIPELINE.md` | live tracker; continuous rewrite | 6K |
| `NORTH_STAR.md` | top goal; changes only in a review session with the user | 2K |
| `SOUL.md` | identity & red lines; changes require explicit user approval | 3K |
| `LEARNINGS.md` | **append-only at bottom**, dated `## YYYY-MM-DD — <lesson>` sections; never rewrite existing learnings | grows |

- Every file carries the Layer-3 header (`updated:`, `maintainer:`). **Single writer** per
  file — two authors inside one lint window is a finding.
- Size budgets are lint-enforced: the whole stack must load cheaply (~20K chars total);
  a bloated STATE.md is a snapshot that stopped being one.
- The archiver never reads this zone (root AGENTS.md reading order — context isolation).
