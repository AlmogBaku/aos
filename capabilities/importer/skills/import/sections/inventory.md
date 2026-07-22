# Stage 1 — Inventory

Enumerate, per the harness cheat-sheet's **Introspection guide**: skills (with their
frontmatter + support files), scheduled jobs (name, schedule, prompt, skills referenced,
delivery), agents/profiles (identity files, config, workspace), context blocks
(SOUL/AGENTS/persona fragments), scripts and plugins, KB conventions the use case relies
on (zones, entry formats), and secrets *referenced* (names only — never open a value).

Record origin/provenance where the harness tracks it (installed-distribution markers,
`x-aos-origin` tags, job name prefixes): anything already owned by an installed
capability is **out of scope** — you import what the user built, not what the kit
installed.

Output: a flat list `<artifact-kind> | <path/id> | <one-line role>` you'll cluster next.
Share it with the user — the inventory is the first thing they can correct cheaply.
