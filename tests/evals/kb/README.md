# kb trigger eval sets

Query sets for measuring whether kb's seven skill descriptions fire on the right prompts.
They exist because **eleven descriptions will eventually compete in one trigger space** —
kb's seven plus work-tracker's five, minus overlap — and that is exactly the case where
authoring intuition fails.

| File | Positives are | Negatives are |
|---|---|---|
| `capture-space.json` | `kb-capture`'s job — the user said something worth keeping | commitments (work-tracker's space), requests to act now, recalls, base-system questions, and the setup skills |
| `setup-space.json` | `kb-init`'s job — no tree exists yet | `kb-adopt`'s job (a tree exists, register in place) and `kb-import`'s (transform content in) — plus captures and recalls |

Two rules these sets follow, both from the
[authoring guide](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):

1. **Queries are concrete and realistic** — file paths, names, casual phrasing, typos, a
   little backstory. `"Format this data"` tests nothing.
2. **Negatives are near misses.** Every negative here shares vocabulary or intent with the
   positives. An obviously-irrelevant negative ("write a fibonacci function") measures
   nothing, so there are none.

## Running

```bash
cd .agents/skills/skill-creator
python -m scripts.run_eval \
  --eval-set ../../../tests/evals/kb/capture-space.json \
  --skill-path ../../../capabilities/kb/skills/capture \
  --runs-per-query 1 --verbose
```

Each query spawns a real `claude -p` subprocess, so cost scales as
queries × runs × iterations. `run_eval.py` also writes a temporary command file into
`.claude/commands/` — gitignored, and therefore invisible to `git status`.

`scripts/run_loop.py` wraps eval → improve → re-eval and needs `--model`; `run_eval.py`'s
`--model` is optional and defaults to the session's model. Prefer `run_eval` for a cheap
signal and reach for `run_loop` only on a description that actually fails.

## Known: the harness could not measure in this environment (2026-07-28)

`run_eval.py` was run against `capture-space.json` and reported 12/20 — **every negative
passing and every positive reading a trigger rate of exactly 0.0**, including
`"note this down — …"` and `"jot down that …"`, which the description names almost verbatim.

A uniform zero across positives is not a discrimination signal, and a control run confirmed
it: the same query scored 0.0 against an unrelated, definitely-present skill. The cause is
structural — `run_eval.py:53` writes the candidate into `.claude/commands/` (a **slash
command**), while its detector at `:80` only counts a trigger when the model calls the
`Skill` tool with that name, or Reads the file. A slash command is not in the `Skill` tool's
registry, so the tool is never called and the rate is 0.0 no matter how good the description
is.

So these numbers say nothing about description quality in either direction, and no
description was changed on the strength of them. Re-run when the harness can observe
triggering (a real skill install rather than a synthesized command file), and prefer doing it
**once over all eleven descriptions** after work-tracker lands its five.

Until then these sets are the durable artifact, and the descriptions are hand-authored to the
guide's shape — third person, `Use when`, and `Do NOT use` wherever a skill competes for a
trigger — which the `aos_lint.gates.retired` gate enforces mechanically (it validates every skill description's shape, not just the retired vocabulary). An independent
`tessl review run quality` pass scored all seven descriptions 85–100%, four of them at 100%.
