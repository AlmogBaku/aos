# work-tracker

Commitments the user must keep themselves. Someone says *"I need to find time to write the
CFP"* → an action page lands in their private commitments base and a calendar block appears in
the same exchange → progress reports move its status → a nightly steward keeps the backlog
honest → completion sets an expiry, so the list has an exit.

It borrows GTD's vocabulary (next-action, waiting-for, someday) and none of its rituals. The
line that shapes the capability is a speech act: *"write the CFP"* is an instruction to the
agent and files nothing; *"I need to find time to write the CFP"* is a commitment. Same words,
different jobs.

Five skills, one agent, one private base, and no queue shared with kb — it composes with kb
only through the `kb` command on PATH.

| Skill | Job |
|---|---|
| `work-tracker` | the map: four statuses, which skill for which job, the authority rules |
| `wt-capture` | a commitment becomes an action page, in under five seconds |
| `wt-schedule` | estimate, link to project, block real time — immediately, not overnight |
| `wt-update` | progress: done, slipped, stalled, abandoned — and the knowledge it carried |
| `wt-steward` | the nightly maintenance pass, and the rule about bothering the user |

Requires [`kb`](../kb/) for storage and the `kb` tool on PATH.

## Support matrix

| Harness | Status | Runner |
|---|---|---|
| Hermes | 🧪 built against the cheat-sheet — live e2e owed | @AlmogBaku |
| NanoClaw (v1+v2), OpenClaw, Nanobot | 🧪 cheat-sheet shipped, research-drafted — no runner yet | — |
| Claude Code, OpenCode | 📋 no sheet yet — the no-cheat-sheet path applies | — |

`calendar.write` is `⚠ via skill` on Hermes, so the no-calendar degraded path is real: actions,
statuses and the steward all work, and there are no blocks.
