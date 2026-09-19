# open-session

A cron transcript lives in an internal session that desktop clients exclude from Recents, so a scheduled
turn can never become a conversation the user opens and replies to. `open-session` gives the cron agent
one job: open a new titled session, send the opening prompt as its hidden first turn, and report the
session id and first reply. The session appears in the user's desktop Recents under the right profile,
opening with the agent's message. It never notifies, conducts the conversation, or reuses a title.

| Runtime | Support | Notes |
|---|---|---|
| Hermes | Full | Verified reference; session appears in Hermes desktop Recents under the profile. |
| Other harnesses | Derived at install | No reference file yet; installer derives the command from the harness CLI and marks it unverified. |
