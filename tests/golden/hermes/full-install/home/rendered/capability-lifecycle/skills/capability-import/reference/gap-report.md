# GAP.md format

One section per finding, ordered by impact on a second user:

```markdown
## <kind>: <one line>
**Where:** <artifact / path>
**What:** <what didn't map>
**Draft handling:** <placeholder / {{mod}} slot / omitted>
**Proposed fix:** <spec change, cheat-sheet addition, or "author decision needed">
```

Kinds: `secret` (name + location, never the value) · `hardcoded-path` · `harness-only`
(no neutral primitive — evidence for §5.2 vocabulary or §2.4 plugins) · `judgment`
(uncertain split calls) · `drift` (live artifacts that contradict each other) ·
`not-imported`.
