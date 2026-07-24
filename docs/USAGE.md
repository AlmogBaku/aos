# Day-to-day usage

You've [installed](INSTALL.md) kb, onboarding, and gtd-capture. This is what living with
them looks like. Everything below is a thing you *say to your agent* — the skills it
loaded at install time do the rest.

## Capture — fire and forget

> capture: renew the passport before the Berlin trip

That's it. A raw file lands in the routed base's `raw/captures/` in under five seconds,
`triage: pending`, deduped by the tool. **Capture never classifies** — no clarifying
questions, no lookups, no "should this be a task?" — all judgment is deferred to the
nightly pass. Routing is deterministic (channel rules, explicit `work:` tags, keywords);
an LLM guess is used only above a confidence bar and never into a shared base.

Works from any channel your harness hears: chat, voice note, forwarded message.

## The nightly rhythm

Two scheduled agents divide the thinking so you don't have to do it at capture time:

| When | Who | What it does |
|---|---|---|
| 23:00 | gtd-capture's **drainer** | Walks pending captures (`base inbox`): actionable ones become next-actions or reminders; two-minute items get flagged; its pass is additive bookkeeping only |
| 23:30 | kb's **archiver** | Promotes the captures that are actually *knowledge* into current-truth wiki pages — skeptical, default-empty — then files the log line; cross-base re-routing proposals land in your review queue |
| (cron) | `base sync` | Rebase-pull/push per base; a conflict aborts safely into `_ops/needs-review.md` — no agent ever resolves your merge |

No cron on your harness? The same runs exist as run-cards: *"drain the inbox now."*

## Recall — ask what you know

> what do I know about the Berlin trip?

The recall skill answers **with citations into your bases** — links to the pages and raw
captures it drew from — and **admits gaps** ("not in the KB") instead of filling them
with plausible inventions. Wiki pages carry current truth only; history lives in git and
`## Timeline` ledgers.

## State — "where's my head?"

Each base keeps one capped `state.yaml` attention window: one-liners pointing into
pages. *"Where do things stand?"* reads them, private bases first. Items age out
(staleness is linted); the cap forces eviction, so the window stays a window.

## Talking to a base directly

The `base` tool is on PATH after install — deterministic, logs every write, never calls
an LLM. The verbs you'll actually type:

```text
base capture --text "…"        # never hand-write into raw/
base inbox [--failed]          # the pending view (the "inbox" is a view, not a file)
base search <term>             # ALWAYS before creating a page — EXISTS means stop
base state add|bump|drop|check # the attention window
base lint                      # the health report (report-only)
base sync                      # pull/push all bases
base --help                    # the rest: links, grants, index, verify, import survey
```

## Tuning and correcting

- **Re-run any interview** — only unanswered questions are asked; `--refresh` re-asks
  everything and shows you the diff before writing.
- **Hand-edit anything materialized** — normal. The agent captures your edits back into
  `MOD.md` when it notices them, so the next upgrade preserves them.
- **`update`** after a `git pull` merges new capability versions under your overlay —
  diff-gated, backed up.
- **Corrections beat re-capture**: told it something wrong? Say so — the page is fixed
  in place (current truth), and git remembers the old state.

## Growing the kit

- Built something in your own harness worth sharing? *"Wrap my <thing> into a
  capability"* — the **importer** inventories it, splits generic mechanism from your
  personal nuance, and emits a draft package + gap report. The PR stays yours to open.
- Keep asking for the same kind of standing automation in chat? **capability-builder**
  notices, and walks it through intake → research → design → your approval → build
  instead of bolting one-off changes onto your harness.

Contributing either output upstream: [CONTRIBUTING.md](../CONTRIBUTING.md).
