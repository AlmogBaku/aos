# Day-to-day usage

You've [installed](INSTALL.md) capability-lifecycle, kb, and work-tracker. This is what
living with them looks like. Almost everything below is a thing you *say to your agent* —
the skills it loaded at install time do the rest. The last section is for when you'd rather
talk to a base directly.

## Capture — fire and forget

> capture: renew the passport before the Berlin trip

That's it. A file lands in the routed base's `.kb/pending/` in under five seconds, deduped
by the tool. **Capture never classifies** — no clarifying questions, no lookups, no "should
this be a task?" — because the one thing capture cannot afford to lose is the thought.
Judgment is deferred to the nightly pass.

Routing is deterministic first (channel rules, explicit `work:` tags, keyword rules); a
model guess is used only above a confidence bar, and **never into a base other people
pull**. Works from any channel your harness hears: chat, voice note, forwarded message.

Later, an agent moves it into `_raw/` with `kb ingest` — one `git mv`, because **location is
the state**. Nothing marks it "triaged"; it either sits in `.kb/pending/` or it doesn't.

## Commitments — said once, blocked immediately

> I need to find time to write the CFP before Friday

Two things happen in the *same exchange*: the commitment is filed as a page under
`actions/`, and time is blocked for it. Not at midnight — now, while you're still there to
say "not Thursday, I'm out".

The distinction that decides whether anything is filed at all is *whose work it is*. "Write
the CFP" is an instruction, and your agent just writes it. "I need to find time to write the
CFP" is a commitment of yours, so it gets tracked. "Robin says the venue is booked" is
knowledge, and goes to your KB instead.

Then, as things move:

> the CFP is done · I'm blocked on Robin's numbers · push the CFP to next week

There is no list file to update, because **a list is a view**: "what's next" is a query over
pages that each carry their own status.

## The scheduled passes

Two agents, three jobs, and none of them is doing work you're waiting on:

| When | Who | What it does |
|---|---|---|
| 23:00 | work-tracker's **steward** | Keeps the backlog honest: overdue, about to expire, stalled, repeatedly-rescheduled, someday gone cold. Adjusts its own bookkeeping silently; **asks** before changing anything you committed to. Silent on a clean night |
| 23:30 | kb's **archiver** | Promotes the captures that are actually *knowledge* into current-truth wiki pages — skeptical, default-empty, because most captures aren't knowledge |
| Sat 07:00 | kb's **archiver** | The weekly `kb lint` pass: mechanical fixes applied, judgment findings filed into `.kb/pending/`, only *Critical* reaches you |
| every 5 min | `kb sync` | Rebase-pull/push per base; a conflict aborts safely and files a `.kb/pending/` entry — no agent ever resolves your merge |

No cron on your harness? The same runs exist as run-cards: *"run the steward now."*

## Recall — ask what you know

> what do I know about the Berlin trip?

The recall skill answers **with citations into your bases** — the pages and raw captures it
drew from — and **admits gaps** ("not in the KB") instead of filling them with plausible
inventions. Wiki pages carry current truth only; history lives in git and `## Timeline`
ledgers.

## State — "where's my head?"

Each person keeps one capped attention window at `.kb/state/<you>.yml`: one-liners pointing
into pages. *"Where do things stand?"* reads them, private bases first. Items age out
(staleness is linted), and the cap forces eviction, so the window stays a window.

## Talking to a base directly

The `kb` tool is on PATH after install — deterministic, one attributed commit per write,
never calls an LLM. Everything your agent does, you can do. The verbs, by what you'd want:

```text
# capture and intake
kb capture --text "…"            # never hand-write into _raw/
kb inbox                         # your pending items waiting on an agent (--all: everyone's)
kb pending list --where waits_on=human   # the queue waiting on YOU
kb pending add --kind finding --body "…" # file something with no artifact of its own
kb ingest <path>                 # pending -> _raw/, as a git mv
kb refuse --path <p> --reason "…"        # record a write you declined, and why

# find things
kb search <term>                 # BM25 full text — ALWAYS before creating a page
kb find --where status=next      # metadata query; --without for absence
kb links <page>                  # backlinks, outbound, orphans
kb history                       # recent activity, from git
kb state add|bump|drop|check|show        # the attention window

# change things (each is one attributed commit)
kb set <page> status=done        # mutate frontmatter
kb verify <page>                 # flip to verified: true, user-confirmed
kb commit --path <p> --verb promote --summary "…"   # attribute a hand-written change
kb archive <page> --reason "…"   # git rm; the history IS the archive
kb prune                         # delete what `expires:` says is over

# the base itself
kb init <name> --path <p>        # scaffold + register a new base
kb adopt <path>                  # register an existing tree; zero writes into it
kb migrate --base <name>         # carry a layout 1 base to layout 2
kb import survey <src>           # bulk import a foreign KB (source read-only)
kb lint                          # the check catalog; report-only
kb grants --subject <s> --verb write --object <o>   # who may do what
kb config get|set <key>          # the base's own config
kb index rebuild                 # regenerate index.md
kb sync --all                    # pull/push every base
kb --help                        # everything, per verb
```

Three sharp edges worth knowing before you type:

- **`kb prune` reads `expires:` and nothing else** — not `status`. An `expires` on a live
  commitment deletes a live commitment. Setting it only when something is finished is a
  discipline you keep, not a promise the tool makes.
- **Values are parsed as YAML**, so `project=[[x]]` quietly stores a nested list. Keep the
  inner quotes: `kb set <page> 'project="[[projects/x]]"'`.
- **Every destructive verb takes `--base`.** Unqualified, it resolves through the registry
  default — which may not be the base you're standing in.

## Tuning and correcting

- **Change how something behaves** — *"make the steward run at 22:00"*. The change is
  applied *and* written into your `MOD.md`, so the next upgrade re-applies it instead of
  reverting you. Adjusting something aos installed is never a new build.
- **Re-run any interview** — only unanswered questions are asked; `--refresh` re-asks
  everything and shows you the diff before writing.
- **Hand-edit anything materialized** — normal. The agent captures your edits back into
  `MOD.md` when it notices them, so the next upgrade preserves them.
- **`update`** pulls fresh upstream, then re-applies your MOD.md to the new capability
  versions — your hand-edits folded in first (MOD states current settings, not a history);
  diff-gated, and every render is a commit in your `personal/` repo (revert = rollback).
- **Corrections beat re-capture**: told it something wrong? Say so — the page is fixed in
  place (current truth), and git remembers the old state.

## Growing the kit

- Built something in your own harness worth sharing? *"Wrap my <thing> into a capability"* —
  **`capability-import`** inventories it, splits generic mechanism from your personal
  nuance, and emits a draft package + gap report. The PR stays yours to open.
- Ask for a standing automation — a nightly job, a recurring reminder, a new persona — and
  your agent stops before building it: *"should we plan this properly?"* Say no and it
  proceeds ad hoc; say yes and **`capability-build`** walks intake → research → design →
  your approval → build, so the thing that lands is a capability rather than a one-off
  bolted onto your harness. One-off tasks never trigger it, and neither does changing
  something aos already installed — that's the first bullet above.
- Not sure a capability is sound? *"review work-tracker"* — **`capability-review`** reads it
  as architecture (flows, decision points, what writes what) before reading it as prose, and
  reports; it fixes nothing.
- That tweak you made just for you may be a missing knob everyone wants. Say *"promote
  this"* — your agent drafts the upstream change (a slot + an interview question; never your
  actual answer), you approve the PR, and once it lands your MOD line retires by itself.
  Unsure it's general? Your agent offers a signal issue instead — the lightest possible
  contribution.

Contributing any of it upstream: [CONTRIBUTING.md](../CONTRIBUTING.md). And your `personal/`
repo is always a respectable place for things to simply stay yours.
