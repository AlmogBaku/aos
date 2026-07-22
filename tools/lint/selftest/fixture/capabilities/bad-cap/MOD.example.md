---
capability: bad-cap
onboarded_version: 0.0.1
answers:
  unknown_answer: 42
secrets:
  api_token: sk-plaintext-value-not-a-reference
---

Example overlay with an answer no question defines and a secret stored as a
scalar value instead of a {store, key} reference.
