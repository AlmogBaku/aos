# entities/ — wiki pages for people, companies, products

- **Current truth only.** Replace facts in place; git is the history. Events go to the
  page's `## Timeline` (added only when the page needs one), each line dated and
  pointing at its raw source.
- Frontmatter per BASE.yaml; agent-created pages start `verified: false`.
- Before creating: `base search "<name>"` — exact/alias hits mean the page exists
  (aliases are cheaper than duplicate pages; merging duplicates is never automatic).
- Page-or-inline: a person mentioned once inline in a meeting page does not need an
  entity page yet.
