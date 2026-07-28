# work-tracker trigger eval sets

Query sets for measuring whether work-tracker's skill descriptions fire on the right
prompts. **Eleven descriptions now compete in one trigger space** — kb's seven plus these
four non-entry ones — which is exactly the case where authoring intuition fails.

| File | Positives are | Negatives are |
|---|---|---|
| `commitment-space.json` | `wt-capture`'s job — the user committed to work of *their own* | the agent's work to do now, knowledge (kb's space), and the three sibling skills that own scheduling, updating and backlog review |

The split these sets encode is a **speech act**, not a topic. *"write the CFP"* and *"I need
to find time to write the CFP"* share every content word and belong to different skills: the
first is an instruction to the agent, the second a commitment to track. That pair is the most
important line in the file — four negatives are deliberately the same sentence stripped of the
commitment, because a description that cannot separate them files the user's chat history as a
task list.

Two rules these sets follow, both from the
[authoring guide](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):

1. **Queries are concrete and realistic** — names, dates, casual phrasing, lowercase. `"Add a
   task"` tests nothing.
2. **Negatives are near misses.** Every negative shares vocabulary or intent with the
   positives. There are no obviously-irrelevant ones, because they measure nothing.

## Running

Same invocation as kb's sets — see `tests/evals/kb/README.md`:

```bash
cd .agents/skills/skill-creator
python -m scripts.run_eval \
  --eval-set ../../../tests/evals/work-tracker/commitment-space.json \
  --skill-path ../../../capabilities/work-tracker/skills/capture \
  --runs-per-query 1 --verbose
```

## Known: the harness still cannot measure in this environment (2026-07-29)

**Unchanged from kb's finding, and it applies to these five descriptions too.**
`run_eval.py:53` writes the candidate into `.claude/commands/` as a *slash command*, while its
detector only counts a trigger when the model calls the `Skill` tool with that name. A slash
command is not in the `Skill` tool's registry, so the trigger rate reads **0.0 for every
positive** no matter how good the description is — Plan 02 confirmed this with a control run
against an unrelated, definitely-present skill.

So no description here was tuned on a measured rate, and none should be. These five were
hand-authored to the guide's shape — third person, `Use when`, and `Do NOT use` naming the
sibling that owns each competing case — and verified with `tessl review run quality`, which
does observe something real. Re-run the trigger measurement **once over all eleven
descriptions** when a harness can watch a real skill install.
