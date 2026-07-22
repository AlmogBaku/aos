# Inbox entry format

One line per capture, appended to the KB's `ops/inbox.md`:

```
- YYYY-MM-DDTHH:MM±TZ [<channel>] (#tag #tag) : <verbatim content>
```

- Timestamp: ISO-8601, minute precision, user's timezone (global MOD.md).
- `[<channel>]`: `[whatsapp]`, `[voice]`, `[chat]`; agent-originated: `[<agent>|<ref>]`.
- Tags: `#lowercase-hyphenated`, one paren group; omit `()` entirely when empty.
- A routing prefix ("work: …") is **consumed**: stripped from content, recorded as its tag
  (`#work`). "Verbatim" applies to everything after the prefix.
- Router `status: uncertain` → append `#kb-routing-uncertain`. Rule/tag-resolved entries
  carry no routing annotation.
- Long content (transcripts, forwarded text > a paragraph): write to `raw/captures/` per
  the KB schema; put a one-line pointer entry here.
- Corrections: never edit an entry — append a new one tagged `#correction`.
- Nothing else goes in the inbox file: no headings, no blank-line groups, no status notes.
