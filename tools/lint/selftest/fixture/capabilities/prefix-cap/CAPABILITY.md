---
id: prefix-cap
version: 0.1.0
tags: [infra]
summary: Plants a malformed skill_prefix, which must not be mistaken for the default.
skill_prefix: Bad_Prefix
skills:
  - id: prefix-cap
    used_by: [main]
---

One violation: skill_prefix is not [a-z0-9-] ending in a hyphen.
