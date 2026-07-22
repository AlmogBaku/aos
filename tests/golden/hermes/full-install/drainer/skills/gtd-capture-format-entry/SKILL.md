---
name: format-entry
description: Composes or edits a single inbox entry line in the canonical format. Use when writing a capture line, appending a tag, or validating that a line parses.
x-aos-origin: gtd-capture@0.1.0
---

# format-entry

The shared grammar both the capture path and the drain speak. The canonical line:

```
- YYYY-MM-DDTHH:MM±TZ [<channel-or-agent|ref>] (#tag #tag) : <content>
```

- **Compose**: build the line mechanically — timestamp (user timezone, minute precision,
  explicit offset), bracket token, tag group (may be empty: `()` is omitted entirely),
  ` : `, verbatim content on one line.
- **Append a tag** (the only legal edit to an existing entry): add inside the existing
  paren group, or insert `(#tag)` before the ` : ` if there was none. Touch nothing else
  on the line.
- **Validate**: a line parses iff it matches `- <ISO-8601±TZ> [<token>] (…)? : <content>`.
  A line that doesn't parse is reported (drain report / lint), never silently rewritten.
- Corrections are new entries tagged `#correction` — there is no other edit operation.
