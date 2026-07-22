# {{kb_name}} — map of content

> The MOC. The archiver keeps this current; humans and agents start here after AGENTS.md.

## Layers

- **Raw sources** — [`raw/`](raw/AGENTS.md): captures · clippings · meetings · emails ·
  calendar. Immutable; promoted nightly.
- **Semantic layer** — [`entities/`](entities/AGENTS.md) (people · companies · communities
  · products) · `concepts/` · `comparisons/` · `queries/` · `projects/` · `domains/`.
- **Current state** — [`state/`](state/AGENTS.md): the live snapshot stack.

## Entry points

- Inbox: [`ops/inbox.md`](ops/AGENTS.md) — the capture front door.
- Review queue: `_ops/needs-review.md` — judgment calls awaiting the user.
- Latest lint report: `_ops/` (`lint-report-YYYY-WW.md`).

## Entity indexes

Rebuilt weekly by the archiver (`_ops/entity-index-<subdir>.md`). Empty until first lint.
