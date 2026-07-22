# karpathy-llm-wiki

The one methodology v0.1 ships (ARCHITECTURE §4.4). The pluggable directory contract a
second methodology would also satisfy:

| part | here | role |
|---|---|---|
| `init/` | `AGENTS.md`, `SCHEMA.md`, `index.md`, `log.md`, `zones/*.AGENTS.md`, `TREE.md` | what `kb init` scaffolds (the shipped `SCHEMA.md` template *is* the methodology's schema fragment — one artifact, not two) |
| `lint/SKILL.md` | 18 deterministic checks | the weekly audit + adopt's divergence report |
| archiver prompts | `archiver/{promote,lint,sync}.md` | the schedules' `prompt_ref` targets (the agent spec itself lives at the capability level: `../../agents/archiver.agent.yaml`) |
| `scripts/kb-sync.sh` | standalone script | rebase-only sync, conflicts surfaced never resolved |

Two pillars: immutable `raw/` → synthesized wiki with `[[wikilinks]]`, plus a
rolling-window `state/` for current truth. Extracted from a live production KB with its
failure modes designed out (lint ships in init and is scheduled immediately, archiver
schedules created in the same session as the tree, log lines are a validated grammar,
drain SLA is a watched number).

## Relation to Karpathy's LLM wiki

Canonical source: [karpathy's `llm-wiki.md` gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
("Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase").

Adopted: immutable read-only `raw/` · LLM-owned wiki pages · `AGENTS.md` as the schema ·
`index.md` catalog + append-only `log.md` · ingest (here: promote) and lint operations ·
query discipline (answer from the wiki; valuable answers become pages).

Divergences: his third layer is the schema file; ours is `state/` (rolling current truth
— the schema ships as `AGENTS.md`+`SCHEMA.md` regardless). Added beyond the gist:
multi-agent grants/authorization, sha256 dedup, growth stages, capture inbox + drain SLA,
the sync loop. Log line is stricter than his `## [date] [op] | [desc]` (five fields,
lint-validated) for the same grep-ability.
