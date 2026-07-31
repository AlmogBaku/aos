# Stage 3 — Design

Synthesize Intake + Research into one proposal — a single artifact the user can
evaluate as a whole, not something absorbed one reply at a time. Shape it like this
repo's own capability one-pagers:

- **Scope** — what it does, one paragraph
- **Depends** — capabilities and host primitives it needs
- **Skills / agents** — what gets materialized, and why each piece exists
- **v0.1 acceptance** — what "done" looks like
- **Open items** — anything Research left unresolved, named explicitly, not buried

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
