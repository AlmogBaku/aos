# Stage 3 — Design

Synthesize Intake + Research into one proposal — a single artifact the user can
evaluate as a whole, not something absorbed one reply at a time. Shape it like this
repo's own capability one-pagers:

- **Scope** — what it does, one paragraph
- **Depends** — capabilities and host primitives it needs, including `capability-lifecycle`
  (and `kb`, when installed and allowed) for an agent whose only audience is the user (below)
- **Each agent's audience and inputs** — who it answers: the user alone, anyone else
  (guests, invited people, group members an authorization plugin lets in), or nobody
  (background-only: it never messages anyone, or only runs on schedule); and whether it
  reads content other people write (fetched pages, inbound mail, group messages)
- **Skills / agents** — what gets materialized, and why each piece exists; for every
  skill and cron job, the agent that runs it (`main` or a named agent), and every other
  capability's skill an agent loads (`uses`)
- **v0.1 acceptance** — what "done" looks like
- **Open items** — anything Research left unresolved, named explicitly, not buried

**An agent whose only audience is the user** can be retuned from its own chat and reads
and files the user's knowledge. A package that ships at least one such agent lists
`capability-lifecycle` in `depends.capabilities`, and `kb` too when `aos-cap list` shows
kb installed. It gets one `uses` row per skill, each naming every such agent in its
`agents:` list: `capability-lifecycle`'s `capability-lifecycle` and `evolve`, and with kb
installed, kb's `recall`, `capture` and `route` (capture and recall both call route).
Write the rows per package, not per agent: a `uses` row whose provider is missing from
`depends`, or a second row for the same skill, fails the manifest.

These skills run commands — `aos-cap`, `kb` — and `evolve` edits the household's MOD
files, so an agent that gets them keeps the terminal and write access to
`<aos_home>/personal/`; the proposal lists that in the agent's tools. If the agent's tools
were merely narrow and it would otherwise have no terminal, granting one for these rows is
part of what the user approves; an agent whose tools were restricted *to contain it* stays
sandboxed (below) and gets none of the rows.

**An agent that reads content other people write** can be steered by those people even
though only the user talks to it. It gets the two `capability-lifecycle` rows as above, but
the three kb rows only after the user answers yes to an open item naming the combination —
the user's knowledge, content others write, and a terminal — for that agent; until then it
is left out of the kb rows' `agents:` lists (and `kb` stays out of `depends` when no other
agent needs it). Describe such an agent's reach by its terminal, not by the skills it
lacks: a terminal runs as the user, so it reads every file the user can — the knowledge
bases on disk and `<aos_home>/personal/` included — and reaches the network. Never call it
contained to its own folder, cut off from the knowledge bases, or unable to send anything
out while it holds a terminal or a web fetch.

This is an allow rule. An agent anyone else can reach, a sandboxed agent (fail-closed
hooks, or a toolset restricted to contain it), and a background-only agent are in none of
those lists: a guest must never retune a capability or read the user's knowledge. Name
each agent's audience, inputs and tools in the proposal, so the user's approval covers
them.

Then the half a feature list leaves out. **A capability is software**, so design it as one:

- **The flow** — the journey end to end, and every point where it branches. Name the
  decision points explicitly; the ones left implicit are where a weaker model improvises.
- **Units vs resources** — the jobs it does, and separately what powers each (skill, agent,
  tool, cron, template, overlay). A job with nothing powering it is a wish; a resource
  serving no job is dead weight, and both are easier to see in two lists than in one.
- **Failure modes** — for each, how it *surfaces*: a crash the user reports, or a quiet
  wrong answer nobody notices. The second kind has to be designed against, not debugged
  later.
- **A diagram**, once there is more than one moving part — mermaid, per the kit's
  convention. Skip it for a single skill with no agent, cron or tool: a two-box diagram
  carries no information. Drawing is how you find out whether the flow above is actually
  understood.

The {{skill: review}} skill checks exactly these afterwards, so writing them now is not
ceremony — it is the difference between review verifying a design and review having to
reverse-engineer one.

Present it, and stop. **Nothing proceeds to Build without the user explicitly
approving this proposal.** Iterate on the proposal itself if they push back — that's a
Design loop, not a failure.
