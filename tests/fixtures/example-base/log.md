# log — example

<!-- Append-only. One line per mutation, written by the `base` tool (manual writes use
     the same grammar). Format:
     YYYY-MM-DDTHH:MM±TZ | <agent> | <verb> | <path> | <one-line summary>
     Verbs: create promote merge archive flag resolve sync-conflict lint route refuse
            capture state verify bootstrap -->
2026-07-23T23:25+03:00 | agent:main | bootstrap | . | base example scaffolded (layout 1)
2026-07-23T23:25+03:00 | agent:main | capture | raw/captures/2026-07-23-choir-fundraiser-note.md | pending: Choir fundraiser note
2026-07-23T23:25+03:00 | agent:main | state | state.yaml | add: Choir fundraiser planning — helping Robin
2026-07-23T23:25+03:00 | agent:main | create | index.md | index rebuilt
