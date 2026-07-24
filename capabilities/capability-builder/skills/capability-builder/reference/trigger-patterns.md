# Trigger calibration — task vs. use case

Fire on requests that would create something persistent or recurring. Never fire on
word choice alone — "add"/"create"/"make" show up in plenty of one-off asks too.

**Fires:**
- "Every morning, can it also check my calendar and warn me about..."
- "Every weekday at 08:00, send me a one-line weather summary"
- "Let's build something that watches my inbox for invoices"
- "Can we make it so whenever someone messages me about X, it..."
- "I keep doing this by hand every week, can we automate it"
- "Remind me every Sunday to water the plants"
- Explicit: "add a skill/agent/capability for..."
- Anything that defines a new persona, a new standing instruction to another agent, or
  a new cron — the interrupt comes BEFORE the cron/automation gets created, never
  after

**Does not fire:**
- "Add this to my calendar for Friday"
- "Create a file called notes.md"
- "Draft an email to X"
- "Make this paragraph shorter"
- Questions about a capability that already exists ("what does the drainer do")

Key on persistence, not ambiguity — an underspecified one-off ask still doesn't fire;
an unambiguous but recurring/systemic ask still does. Gate everything and the user
stops reading what they approve, which is worse than gating nothing.

Decline once → drop it for that request, don't re-offer mid-conversation. The same
shape of ask resurfacing later is a fresh trigger, not nagging.
