# Inbox entry format

One line per capture, appended to the KB's `ops/inbox.md`:

```
- YYYY-MM-DDTHH:MM±TZ [<channel>] (#tag #tag) : <verbatim content>
```

- Timestamp: ISO-8601 to the minute, explicit UTC offset, the user's timezone (global
  MOD.md).
- `[<channel>]`: where it arrived — `[whatsapp]`, `[voice]`, `[chat]`; agent-originated
  entries use `[<agent>|<ref>]`.
- Tags: zero or more `#lowercase-hyphenated` in one paren group. The user's explicit
  routing prefix ("work: …") becomes the routing tag; uncertain routing appends
  `#kb-routing-uncertain`.
- ` : ` separates metadata from content. Content is verbatim, one line no matter how long.
- **Long content** (transcripts, forwarded text > a paragraph): write it to the KB's
  `raw/captures/` as its own file per the KB schema and put a one-line pointer entry here
  instead. The inbox holds lines, never documents.
- **Corrections are appends**: never edit an earlier entry — add a new one tagged
  `#correction` that supersedes it.
- Nothing else goes in the inbox file: no headings, no blank-line groups, no status notes.
