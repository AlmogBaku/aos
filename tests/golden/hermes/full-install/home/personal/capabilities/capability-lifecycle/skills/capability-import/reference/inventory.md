# Stage 1 — Inventory

Enumerate per the cheat-sheet's Introspection guide: skills (frontmatter + support
files), scheduled jobs (name, schedule, prompt, skills, delivery), agents/profiles,
context blocks (SOUL/AGENTS/persona fragments), scripts and plugins, KB conventions the
use case relies on, secrets *referenced* (names only).

Exclude anything owned by an installed capability (origin tags, `aos:` job prefixes,
distribution markers) — import what the user built, not what the kit installed.

Output: `<kind> | <path/id> | <one-line role>` list. Show it to the user before
clustering.
