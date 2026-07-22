---
name: format-entry
description: Composes or edits a single inbox entry line in the canonical format. Use when writing a capture line, appending a tag, or validating that a line parses.
---

# format-entry

Canonical line:

```
- YYYY-MM-DDTHH:MM±TZ [<channel-or-agent|ref>] (#tag #tag) : <content>
```

- **Compose**: timestamp (user timezone, minute precision, explicit offset) + bracket
  token + tag group (omit `()` when empty) + ` : ` + content on one line.
- **Append a tag** — the only legal edit: add inside the existing paren group, or insert
  `(#tag)` before ` : ` if absent. Touch nothing else on the line.
- **Validate**: a line parses iff it matches `- <ISO-8601±TZ> [<token>] (…)? : <content>`.
  Non-parsing lines are reported (drain report / lint), never silently rewritten.
- Corrections are new entries tagged `#correction`. There is no other edit operation.
