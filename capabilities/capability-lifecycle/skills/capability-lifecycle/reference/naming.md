# Naming and skill identity

Binds anyone authoring or installing a capability. The lint code after each rule is what
enforces it in the kit's CI (`node tools/lint/aos-lint.mjs`); this file is the same rules at
runtime, where CI cannot reach. If the two ever disagree, the code is the bug.

## Contents

- What to name things
- Installed names — the identity that ships
- Uniqueness is a gate, not a convention
- Agent Skills conformance
- Where `skill-creator` fits

## What to name things

- **Skills are action-oriented**: `install`, `evolve`, `drain`, `route`. A skill is a job
  the agent does.
- **Agents are role-oriented**: `archiver`, `drainer`, `librarian`. An agent is someone who
  holds a job.
- **The entry skill is the exception**: it is named after its capability (`kb`,
  `gtd-capture`), because it is the capability's front door, not one of its jobs.
  (`structure/entry-skill`)
- Never a vague name (`helper`, `utils`, `tools`) and never a bare noun (`documents`,
  `data`). Pick one pattern per capability and hold it.

## Installed names — the identity that ships

A skill id is **capability-local**. The name a harness sees is computed:

```
prefix         = skill_prefix from CAPABILITY.md, if declared and non-empty
                 else "<capability-id>-"
installed name = the id, if it is the capability id           (the entry skill)
                 the id, if it already starts with the prefix (never doubled)
                 prefix + id, otherwise
```

`aos-lock skills <cap-dir>` prints the mapping; it is the only sanctioned way to compute
it. Write bare ids — an id that already carries its prefix is an error, not a shortcut
(`skills/prefix-redundant`), and a malformed `skill_prefix` is too (`skills/prefix-format`).

Consequences that bite if you forget them:

- **The render directory and the symlink both use the installed name**, and so does the
  render's frontmatter `name`. One identity, every harness — no per-harness rewriting.
  `aos-lock render` does this; do not hand-copy a skill.
- **Cross-skill references in prose use the installed name.** References resolve by name at
  runtime, and the bare id names nothing once installed — say `kb-route`, not `route`.
  (`skills/ref-unqualified`)
- The `metadata.aos.origin` stamp is added by `aos-lock render` at install and never shipped
  upstream. (`skill/origin-tag`)

## Uniqueness is a gate, not a convention

Harnesses keep **one flat skill namespace**. Two skills with one name is a silent override,
so a skill name is single-owner — the same rule schedules have (§5.5).

- In the kit, two capabilities computing the same installed name is an error.
  (`skills/installed-collision`)
- At install, `aos-lock --home <home> skills <cap-dir> --check --harness-skills <dir>…` is
  the gate. On a harness that installs skills as flat `<name>.md` files (Nanobot), pass the
  same directory — the gate reads both forms. It
  checks three places: every capability in the household, the skill links the lockfile
  records for other capabilities, and the skills the harness already has — including ones
  aos never installed. Exit 17 means a collision; the report names the owner.
- **Never resolve a collision by renaming at install time.** The name is part of the
  package: fix it upstream (`capability-contribute`), or in the user's own capability
  (`capability-evolve` → the source, not the overlay). Renaming locally would make the
  user's harness disagree with everyone else's.
- Links this capability already owns are exempt, so re-installing and upgrading are clean.
- **Read the `checked:` lines it prints.** A clean result names every source it consulted,
  and says so in capitals when one could not be reached (no household resolved, no
  `--harness-skills` given). "Clean" against two of three sources is not clean — pass
  `--home` and the harness's skills dirs.

## Agent Skills conformance

Every `skills/<id>/` folder must stand alone as a valid Agent Skills folder:

- `name` ≤64 chars of `[a-z0-9-]`, equal to the directory name, and free of the reserved
  words `anthropic` and `claude`. The limits apply to the **installed** name, since that is
  what ships. (`skill/name`, `skill/name-dir`, `skill/reserved-word`, `skills/installed-name`)
- `description` non-empty, ≤1024 chars, third person, and it says both what the skill does
  **and when to use it** — it is the only thing loaded until the skill triggers.
  (`skill/description`, `skill/description-when`)
- **No angle-bracket tags in `name` or `description`.** Both are injected into the system
  prompt, where `<capability>` reads as markup; put placeholders in the body.
  (`skill/xml-tags`)
- Frontmatter carries spec fields only — `name`, `description`, `license`, `allowed-tools`,
  `metadata`, `compatibility`. Harness-specific keys go under `metadata`.
  (`skill/unknown-key`)
- SKILL.md body under 500 lines; depth goes in a sibling `reference/`, **one level deep**.
  A reference file may not link to another reference file — a file reached through a file
  gets read only in part. (`skill/body-length`, `skill/nested-reference`,
  `skill/no-cross-path`)
- A reference file over 100 lines opens with a `## Contents` block, so a partial read still
  shows its scope. (`skill/reference-toc`)
- Scripts are executed, never loaded as context. Say which you mean: "run
  `analyze.py`" vs "see `analyze.py` for the algorithm". Forward slashes in every path.
- `used_by` names only this capability's own agents (or `main`), and every skill declares
  it — an agent never loads a skill it was not given. (`skill/used-by`, `skill/used-by-ref`)

## Where knowledge goes — only the skill folder travels

An installed skill is a folder in a flat set of skills. There is no capability beside it,
no package root, no sibling `harnesses` or `tool` directory. So **a shipped skill may only
reference paths inside its own folder** — `reference/`, `scripts/`, `templates/`. Anything
else sends the agent hunting for a path that exists in the source tree and nowhere on the
machine it is running on.

Three ways to reference something, and they cover every case:

| What you need | How to write it |
|---|---|
| depth for this skill | a plain relative path — `reference/naming.md`, `scripts/check.py` |
| another skill, or knowledge it owns | name the skill (`capability-lifecycle`), then its own path (`reference/overlay.md`) — the agent loads the skill, and the path resolves inside it (`skill/no-cross-path`) |
| something in the household | write it from a root — `<home>/upstream/capabilities/<id>/…`, `<home>/personal/…` — which does resolve at runtime |

Consequences worth stating, because each one was a real bug:

- **Package-level knowledge belongs in a `reference/` file of the skill that reads it**, not
  in a capability-level directory. That is why the per-harness cheat-sheets are
  `reference/harness-<runtime>.md` here, and not a file in a capability-level `harnesses`
  directory: that shape resolved for the installer reading the clone, and for nobody else.
  (`skill/package-path`)
- **A `reference/` file may not link a sibling `reference/` file.** A file reached through a
  file gets previewed (`head -100`), not read — so the chain silently truncates.
  (`skill/nested-reference`)
- **Never a parent-directory reference.** The materialized directory carries the installed
  name, not the source id, so climbing out of the skill folder breaks even when the path
  looks right in the repo. (`skill/no-cross-path`)
- When you write a path for the *user's* tree — a KB's `_ops/needs-review/`, a draft's
  `agents/<name>.agent.yaml` — say once which root it is relative to. Those are data
  locations, not load targets, and an unrooted one is a guess.

## Where `skill-creator` fits

Anthropic's `skill-creator` skill is installed alongside this capability (see its
CAPABILITY.md) and owns **generic skill craft**: drafting a skill, tuning a description for
triggering, running evals, packaging. Use it when writing or improving a skill's content.

It knows nothing about aos, so this file owns everything above: installed names and the
prefix, the uniqueness gate, action-vs-role naming, the entry-skill rule, `used_by`
scoping, `{{mod}}` slots, and the overlay family. **Where the two disagree about a name,
this file wins** — aos installed names are computed, not chosen. If `skill-creator` is
absent (no network, no plugin mechanism), nothing here changes; it is an aid, not a gate.
