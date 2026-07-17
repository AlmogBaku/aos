# RFC-005: MOD.md persistence model

**Status:** open · **Decides:** how users' co-located `MOD.md` files are versioned and survive `git pull`

## Question

`MOD.md` files live inside the user's clone of the capabilities repo, next to what they personalize (ARCHITECTURE §3.1). Upstream never contains those paths — so `git pull` can't conflict with them. But how does a *user* keep history and avoid losing them?

## Options

1. **Tracked in a private fork:** each user's clone is a private fork; `MOD.md` files are committed there. Your nuances get real git history, machine sync for free, disaster recovery. Upstream CI rejects `MOD.md` in PRs; contributions go up from clean branches. Cost: everyone maintains a fork + must keep contribution branches clean (tooling can help: `aos contribute` creates a clean branch).
2. **Gitignored + `aos backup`:** upstream `.gitignore` excludes `MOD.md`; files stay untracked. Dead simple, zero fork discipline. Cost: no history, `git clean -x` or a re-clone silently destroys personalization; backup is a bolt-on you must remember (or cron).
3. **Nested private overlay repo:** `MOD.md` files sym/copied from a private repo overlaid on the clone. Max separation; most moving parts; symlink fragility.

## Trade-off in one line

Option 1 buys durable history at the cost of fork discipline; option 2 buys simplicity at the cost of a footgun (`git clean` eats your nuances).

## Recommendation

Deliberately none — the group splits on this and both models are livable. One datapoint to gather before deciding: run both for two weeks during reference-capability development and count incidents (lost files, dirty PRs).

## Process

Decide by evidence per RFC-003; deadline starts once two members have run each model.
