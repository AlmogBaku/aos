# Skill quality rubric — the eight judgment dimensions

## Contents
- How to use this (and how not to)
- The mechanical half is already the linter's
- Content: conciseness · actionability · workflow clarity · progressive disclosure
- Description: specificity · completeness · trigger terms · distinctiveness
- Calibration: what this rubric catches that a density metric does not
- Worked verdicts from this kit

## How to use this (and how not to)

Reverse-engineered from repeated external quality reviews of this kit's own skills, so the
knowledge lives here rather than in a tool the kit would depend on. Apply it as a **reviewer's
rubric**, in step 6d.

**Score it as a floor, never a ceiling.** A weak dimension means something is genuinely wrong and
worth fixing. A strong one means stop. There is no value in polishing a skill that already reads
well, and real harm in it: past roughly nine of every ten points, the only remaining moves are
deleting reasoning — the *why* behind a rule, the worked instance of the failure it prevents, the
phrase that signals "do not skip this." Those look like padding to a scorer measuring density and
are exactly what lets a model generalise to a case the rule does not literally cover.

This happened to this very skill. An external scorer flagged *"reviewing it sentence-by-sentence
finds typos; reviewing it as a system finds the defects that matter"* as persuasive rather than
instructional. That sentence is the skill's entire argument for its own step ordering — an
ordering two real runs had just proven correct. Cutting it scored better and reviewed worse.

**The target is task achievement.** Ask "would an agent following this reach the goal?" not "does
this read tightly?" When the two disagree, achievement wins.

## The mechanical half is already the linter's

Do not re-check by hand what `aos-lint` fails the build over — frontmatter parses, `name` matches
its directory and is 1–64 chars of `[a-z0-9-]`, `description` is 1–1024 chars, no XML tags, no
unknown keys, no reserved words, references one level deep with no chains, `## Contents` past 100
lines, body under 500 lines, links resolve, and every declared skill has a directory.

If a review is spending time there, it is duplicating a gate. Spend it on the eight below, which
no validator can reach.

## Content — four dimensions

**Conciseness.** Does it assume the reader is already competent? Explaining what git or markdown
*is* wastes context. But reasoning is not padding: "why" earns its tokens when it lets the reader
handle an unlisted case, and a rule stated bare is a rule that gets skipped under pressure. The
test is not length — it is whether cutting a sentence would change behaviour. If it would, keep it.

**Actionability.** Real commands with real flags, real paths, copy-pasteable. `kb find --where
'expires<today+7d'` beats "query by expiry". A step that says "handle errors appropriately" is not
a step. Watch for the specific failure this kit keeps hitting: a documented command that does not
exist, or exists without the flag named.

**Workflow clarity.** Sequenced steps, a validation checkpoint after anything fragile, and a
feedback loop where output quality matters (run validator → fix → repeat). Destructive operations
need an explicit before-and-after: dry-run, read the list, then act, then confirm what happened.
A multi-step procedure with no checkpoints will have steps silently skipped.

**Progressive disclosure.** An overview that points to depth, not a wall. References one level
deep — a reference that links a sibling reference gets partially read, which silently truncates.
A small single-purpose skill needs no bundle at all; adding one to look thorough is the write-only
artifact problem.

## Description — four dimensions

The description is the *only* thing loaded before the skill triggers, so it is doing selection
work among a hundred others. Third person always: it is injected into a system prompt, and "I can
help you…" or "You can use this to…" causes discovery problems.

**Specificity.** Several concrete actions, not a domain noun. "Extracts text and tables, fills
forms, merges documents" beats "helps with PDFs". Vague descriptions lose to specific ones.

**Completeness.** Both halves, explicitly: *what it does* and *when to use it*. A description
that only says what it does forces the model to guess the trigger.

**Trigger term quality.** The words a user would actually type, quoted where possible — "remember
that…", "note this down", "adopt ~/my-kb". System-internal jargon ("confidence-gated model call")
describes the mechanism to someone who already knows it exists, which is not who is being matched.

**Distinctiveness / conflict risk.** A clear niche, and where a skill competes for a trigger
space, an explicit negative naming the sibling that should win: *"Do NOT use to file something the
user just said — that is kb-capture."* Skills sharing a namespace without negatives mis-fire in
both directions. Only add a negative where competition is real; an obviously-irrelevant exclusion
tests nothing.

## Calibration: what this rubric catches that a density metric does not

Scored four skills (`capability-install`, `capability-evolve`, `kb-route`, `kb-import`) with this
rubric, and separately with the external scorer it was reverse-engineered from. Rankings agreed;
the rubric scored 4–8 points lower on each, which is the right direction for a floor.

The useful result is not the numbers. **The scorer found zero actionable defects. The rubric
found three, and two independent runs of it converged on the same two.** All three were real and
all three are now fixed:

- `evolve`'s capture mode said "step 3 is skipped" where step 3 held both the MOD write and the
  render apply — so a literal follower wrote no overlay statement and then announced that it had.
  **Fluent prose, self-contradicted in one sentence.** Caught by *workflow clarity*.
- `import` said to add directories to the survey's skip list and re-run. There is no such flag;
  the list is a module constant. The surrounding diagnosis was exact, which makes it worse — the
  agent trusts it, then cannot act. Caught by *actionability*.
- `route`'s refusal write dropped `--base`, so the record landed in the registry default in the
  one case where routing had just established it could not choose a base. Caught by
  *workflow clarity*.

The pattern: a density metric rewards text that reads tightly, and all three of these read
tightly. What a rubric aimed at **task achievement** asks instead is "would an agent following
this reach the goal?" — which is how a contradiction and an impossible instruction surface.

Two things the calibration runs deliberately left alone, and were right to: `install`'s thinner
description, and the install/upgrade/onboard trigger overlap. Real as relative scores, already
absorbed by the entry skill's routing table and install's own step 2 — editing them is the polish
the floor rule forbids.

## Worked verdicts from this kit

Real findings, kept as calibration:

- **`route`'s description** scored well on mechanism and poorly on triggers: it said
  "confidence-gated model call across private bases only" — accurate, and not a phrase any user
  types. Adding "file this in the right base", "which base does this belong in" fixed it without
  removing the mechanism.
- **`init`'s workflow** deferred schedule creation entirely to a cheat-sheet, so the step was not
  executable as written. Inlining the three jobs and their ids fixed actionability; the cheat-sheet
  still owns the per-harness syntax.
- **`kb`'s destructive verbs** were listed as bare actions. `kb prune` deletes pages and resolves
  its base from the *registry default* when `--base` is omitted, so the fix was an explicit
  `--base`, a dry-run first, and reading what came back — a workflow-clarity fix, not a wording one.
- **This skill** lost, then regained, the sentence carrying its own ordering argument. The score
  went up when it was cut. The review got worse.
