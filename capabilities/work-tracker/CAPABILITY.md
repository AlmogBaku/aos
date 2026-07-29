---
id: work-tracker
version: 0.1.0
tags: [usecase]
summary: Commitments the user must keep themselves — captured as they speak, scheduled immediately, maintained nightly, and completed with an exit.
depends:
  capabilities: [kb, capability-lifecycle]
  host:
    cron: preferred
    messaging.inbound: preferred
    messaging.outbound: preferred
    calendar.read: preferred
    calendar.write: preferred
skill_prefix: wt-
skills:
  - id: work-tracker
    used_by: [main, steward]
  - id: capture
    used_by: [main]
  - id: schedule
    used_by: [main]
  - id: update
    used_by: [main]
  - id: steward
    used_by: [steward]
schedules:
  - id: nightly-steward
    cron: "0 23 * * *"
    agent: steward
    prompt_ref: agents/steward/nightly-steward.md
    degraded: manual
kb:
  zones:
    - path: "actions/**"
      owner_agent: steward
    - path: "projects/**"
      owner_agent: steward
---

# work-tracker — installer's briefing

*(Consumed at install and not used afterwards. The runtime face of this capability is the
`work-tracker` entry skill.)*

## What this is

Work only the user can do. It borrows GTD's vocabulary — next-action, waiting-for, someday —
and none of its rituals: contexts died with the smartphone, the weekly review existed because
nothing was watching, and a standalone list *file* is a view of a query pretending to be a
store.

The line that shapes everything else is a **speech act**, not a topic. *"Write the CFP"* is
an instruction to the agent, which does it and files nothing. *"I need to find time to write
the CFP"* is a commitment, which becomes a page. Same content words, different skills.

## What you materialize, and why

1. **Skills** per `used_by`. The `work-tracker` entry skill goes to the front agent **and**
   the steward — it carries the map and the authority rules both need. `wt-capture`,
   `wt-schedule` and `wt-update` are the front agent's conversational paths. `wt-steward` is
   the steward's judgment skill, and it stays a real loadable skill rather than folding into
   the schedule prompt because the user triggers it ad hoc (*"tidy my backlog"*), not only
   nightly.
2. **The steward agent** (`agents/steward.agent.yaml`), per the cheat-sheet. Its prompt body
   is `agents/steward/nightly-steward.md`.
3. **One schedule.** `nightly-steward` defaults to 23:00; the user's `steward_hour` answer
   overrides the cron at materialization. Degrades to `manual` without cron.
4. **Base changes — four of them, and all four are load-bearing.** See below.

## The base: exactly one, and it must be private

**The base's registry `name` must literally be `commitments`**, because every skill invokes
`kb --base commitments <verb>` and `--base` matches the registry's `name` field and nothing else —
not a tag, not an alias. Point it at an existing private base or create one:

```
kb init commitments --path <path> --audience private --purpose "commitments I have to keep"
```

Reusing a base the user already has instead? It has to be renamed to `commitments`, or every
command in all five skills exits 1 with `unknown base 'commitments'`. Do not paper over that
by editing the skills — the name is the contract.

Three reasons, and the first is not stylistic:

- **Agent writes into a shared base are proposals in a review queue, never direct.** A
  nightly pass filing five actions there would create five review items instead of doing its
  job.
- Routing by content would **scatter the list across bases** — `resolve_base` picks exactly
  one — so the answer to *"what am I working on"* would depend on which base you asked.
- A personal backlog does not belong in a repo colleagues pull.

**So work-tracker never calls `kb-route`.** Routing places knowledge; a commitment is a fact
about your week, and there is no decision to make.

## The four install-time base changes

Propose all four in the same owner-approved diff. Getting any of them wrong fails *quietly*,
which is why each is spelled out:

1. **Declare the zone** — `zones.actions: {kind: wiki}` in `.kb/base.yml`. Until this exists
   the directory is **invisible**: `kb find` returns nothing and `kb lint` says nothing, both
   with exit 0, because the tool only walks declared zones. This is not tidiness; it is the
   difference between a tracked commitment and a file nothing ever reads again.
2. **Add the type** — append `action` to the base's `types:` list, or every page draws a
   `type 'action' not in base.yml types` finding *once the zone exists*. Before that it draws
   nothing at all, for the reason above: the two omissions compound into total silence.
3. **Declare eight extensions** — `due estimate block slipped since waiting_on status
   project` in `frontmatter.extensions`. The page schema is closed, so a field that is not
   declared is a finding on *every* action page. `status` and `project` are as undeclared as
   the six bookkeeping fields; a six-field list looks like a broken install.
4. **Append two grant rows**, each with `via: work-tracker@0.1.0` so revocation is
   mechanical:

   | subject | object | verbs | notes |
   |---|---|---|---|
   | `agent:main` | `actions/** index.md` | write | the live commitment path (`wt-capture`, `wt-schedule`) |
   | `agent:steward` | `actions/** projects/** index.md` | write | nightly maintenance; project links |

   **Both rows, not one.** `wt-capture` is `used_by: [main]`, so the *front* agent writes
   action pages during an ordinary conversation while the steward writes overnight. Granting
   one leaves the other's writes as grants-audit criticals — and that failure mode is silent:
   the write succeeds, the commit lands, and the weekly lint surfaces it days later.

   **`index.md` is on both rows and is easy to miss.** kb's seed grants it to
   `agent:archiver` alone, but a new page is invisible on the map until the index lists it, so
   both of these agents run `kb index rebuild` — and without the grant every rebuild is a
   grants-audit critical of exactly the silent kind described above.

The `projects/**` row is the steward's alone, because linking an action to its project is
maintenance rather than capture.

## Degraded paths, which are real rather than theoretical

- **No calendar** (`calendar.write` is `⚠ via skill` on Hermes — present only if a calendar
  skill is installed): actions, statuses, deadlines and the whole steward pass still work.
  There are no blocks. `wt-schedule` must **say so** rather than silently doing nothing, and
  an unscheduled action is found by the steward's `--without block` backstop rather than lost.
- **No cron**: `nightly-steward` becomes an invocable run-card. The user asks for it.
- **No sub-agents**: `wt-schedule` runs inline and says which happened.
- **No outbound messaging**: reminders appear in the steward's report instead.

`messaging.inbound` is `preferred`, not `required` — the previous design required it, which
meant a harness with no inbound channel could not install a capability whose whole point
works from the chat you are already in.

## Contracts to preserve

- **Capture and scheduling both happen now, not overnight.** A block that appears at midnight
  is worthless to someone who said *"tomorrow"*.
- **The steward never does work the user is waiting on.** It maintains; it does not capture or
  schedule.
- **An action page holds a commitment, never knowledge**, so it is never the only copy of
  anything — which is what makes `kb prune` safe. `wt-update`'s third step is where that is
  paid for.
- **`due` is a deadline; `expires` is an end of life.** Only `expires` deletes.
- **No ordering contract with kb.** Commitments go straight to action pages and never enter
  `.kb/pending/`, so nothing here shares a queue with kb's archiver. There is no sequencing to
  preserve between the two nightly jobs.

## Contested core — none

work-tracker takes no position on RFC-006 (multi-KB routing/authorization): it uses exactly
one base and never routes. Its composition with kb is through the `kb` command on PATH and
nothing else, which is the arrangement RFC-009 leaves open — no skill here references a kb
skill directly.
