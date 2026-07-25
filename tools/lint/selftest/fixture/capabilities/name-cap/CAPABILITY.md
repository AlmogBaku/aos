---
id: name-cap
version: 0.1.0
tags: [infra]
summary: Plants the skill-identity violations — the installed name is the shipped identity (§2.5).
skill_prefix: bad-cap-
skills:
  - id: name-cap
    used_by: [main]
  - id: bad-cap-sorted
    used_by: [main]
  - id: capture
    used_by: [main]
  - id: claude-helper
    used_by: [main]
  - id: refer
    used_by: [main]
---

Planted here: an id that already carries its prefix, an installed name that collides
with bad-cap's, a reserved word, an XML tag in a description, an unqualified sibling
reference, a nested reference, and a TOC-less long reference.
