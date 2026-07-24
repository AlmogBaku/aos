# Stage 2 — Research

Investigate before committing to a design. Spawn subagents for each open question from
Intake that needs looking into rather than guessing:

- **Reuse** — does an installed capability already cover part of this? Survey
  `capabilities/*/CAPABILITY.md` summaries and entry-skill descriptions.
- **Feasibility** — does the target harness actually support what this needs? Check
  its `CHEATSHEET.md` primitive mapping and Feature notes table for any
  `depends.host` item this would need.
- **Precedent** — is there a close structural analog already built? Read it before
  inventing a new shape.

Checkpoint back to the user after research returns: what was found, what's still open,
anything that changes the shape of the ask. Research agents report findings; they never
write capability files.

Move to Design once the open questions are answered enough to propose something
concrete — not necessarily all of them; unresolved ones become explicit open items in
the proposal.
