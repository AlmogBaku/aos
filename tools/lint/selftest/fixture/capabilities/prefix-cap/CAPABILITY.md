---
id: prefix-cap
version: 0.1.0
tags: [infra]
summary: Plants a malformed skill_prefix and an all-main scoping where a role existed.
skill_prefix: Bad_Prefix
skills:
  - id: prefix-cap
    used_by: [main]
  - id: tidy
    used_by: [main]
---

Two violations: skill_prefix is not [a-z0-9-] ending in a hyphen, and every skill is
scoped to main while a `janitor` agent exists — which is what makes skill/all-main a real
question here rather than an unanswerable one.
