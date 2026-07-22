# karpathy-3layer

The one methodology v0.1 ships (ARCHITECTURE §4.4). The pluggable directory contract a
second methodology would also satisfy:

| part | here | role |
|---|---|---|
| `init/` | `AGENTS.md`, `SCHEMA.md`, `index.md`, `log.md`, `zones/*.AGENTS.md`, `TREE.md` | what `kb init` scaffolds (the shipped `SCHEMA.md` template *is* the methodology's schema fragment — one artifact, not two) |
| `lint/SKILL.md` | 18 deterministic checks | the weekly audit + adopt's divergence report |
| archiver prompts | `archiver/{promote,lint,sync}.md` | the schedules' `prompt_ref` targets (the agent spec itself lives at the capability level: `../../agents/archiver.agent.yaml`) |
| `scripts/kb-sync.sh` | standalone script | rebase-only sync, conflicts surfaced never resolved |

Two pillars: immutable `raw/` → synthesized wiki with `[[wikilinks]]` (Karpathy KB
methodology), plus a rolling-window `state/` for current truth. Extracted from a live
production KB — with its failure modes designed out: lint ships in init and is scheduled
immediately, the maintainer's schedules are created in the same session as the tree, the
log line is a grammar the lint validates, and the drain SLA is a watched number.
