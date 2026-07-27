"""`sync` — ff-pull then merge on divergence, push with jittered retry; conflict ->
safe abort + pending entry + exit 3. Never calls an LLM.

Isolated from every other verb because it is the one place in the tool with real
subprocess/retry/timing concerns (jitter, backoff, sequencer-state detection) and the
one verb that operates across *multiple* bases via the registry (`--all`) rather than
a single resolved `Base`."""

import os
import random
import subprocess
import sys
import time
from pathlib import Path

from ..identity import (
    agent_subject, agent_email, is_repo, git, sequencer_state, resolve_principal,
    principal_name,
)
from ..registry import load_registry
from ..base import Base, resolve_base


def sync_jitter() -> float:
    """Five-minute crons fire on wall-clock boundaries, so N machines collide
    systematically rather than rarely. Only the unattended path waits — an interactive
    `kb sync` should not sit there for no reason."""
    return random.random() * 20


def _remote_ref_missing(proc) -> bool:
    s = (proc.stderr or "").lower()
    return "couldn't find remote ref" in s or "no such ref" in s


def _sync_one(root: Path, name: str, agent: str = "agent:main",
              author: tuple[str, str] | None = None, attempts: int = 3) -> int:
    # Never touch a worktree that is mid-operation. `git add -A` here would stage the
    # conflict-marker versions and commit them, and git then refuses to start another
    # operation over the leftover state — so every later tick fails too, silently,
    # forever. Checking first turns that into one loud, recoverable message.
    seq = sequencer_state(root)
    if seq:
        print(f"{name}: git is mid-{seq} — refusing to sync until that is resolved "
              f"(`git {'rebase' if 'rebase' in seq else 'merge'} --abort`)",
              file=sys.stderr)
        return 5

    base = Base(root, check_layout=False) \
        if (root / ".kb" / "base.yml").exists() else None

    # Sweep anything written outside a tool verb — an agent editing a wiki page by
    # hand. Data safety comes first, so it is committed rather than refused, but the
    # `sweep:` subject marks it as unattributed so lint reports it instead of letting
    # it pass as an ordinary attributed write.
    git(root, "add", "-A")
    if git(root, "diff", "--cached", "--quiet").returncode != 0:
        n = len(git(root, "diff", "--cached", "--name-only").stdout.splitlines())
        env = dict(os.environ)
        env["GIT_COMMITTER_NAME"] = agent
        env["GIT_COMMITTER_EMAIL"] = agent_email(agent)
        env["GIT_AUTHOR_NAME"], env["GIT_AUTHOR_EMAIL"] = (
            author if author and all(author) else (agent, agent_email(agent)))
        r = subprocess.run(
            ["git", "commit", "-q", "-m",
             f"sweep: {n} path{'s' if n != 1 else ''} written outside a verb"],
            cwd=root, capture_output=True, text=True, check=False, env=env)
        if r.returncode:
            print(f"{name}: commit failed", file=sys.stderr)
            return 2

    if git(root, "remote", "get-url", "origin").returncode != 0:
        print(f"{name}: synced (no remote)")
        return 0

    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for attempt in range(1, attempts + 1):
        # Fast-forward where possible; only genuinely diverged history needs a merge.
        # Rebase is deliberately not the default: it rewrites commits another machine
        # may already hold, and a conflicted rebase leaves state that blocks every
        # later tick. Both tools that run unattended across many machines — Obsidian
        # Git and git-annex — made the same call. A braided history nobody reads is a
        # cheaper price than a sync loop that stalls.
        pull = git(root, "pull", "--no-stat", "--ff-only", "origin", branch)
        if pull.returncode != 0 and not _remote_ref_missing(pull):
            pull = git(root, "pull", "--no-stat", "--no-rebase", "--no-edit",
                       "origin", branch)
        if pull.returncode != 0 and not _remote_ref_missing(pull):
            git(root, "merge", "--abort")
            if base:
                entry = base.pending_add(
                    "conflict", "human", f"sync conflict ({name})",
                    "`git pull` hit a conflict and was aborted cleanly. The base is "
                    "consistent but behind its remote — resolve by hand, then push.",
                    agent)
                base.commit("sync-conflict", entry,
                            f"{name}: pull aborted, needs a human", agent, author)
            print(f"{name}: sync conflict — aborted clean, surfaced to review queue",
                  file=sys.stderr)
            return 3
        if git(root, "push", "-q", "origin", branch).returncode == 0:
            print(f"{name}: synced")
            return 0
        # Lost the push race — someone pushed between our pull and our push. With
        # several machines on one interval the ticks land on the same wall-clock
        # second, so this is systematic rather than rare; jittered backoff is what
        # breaks the lockstep.
        if attempt < attempts:
            time.sleep(min(2 ** attempt, 8) + random.random())
    print(f"{name}: push failed after {attempts} attempts", file=sys.stderr)
    return 4


def cmd_sync(args):
    reg = load_registry(args)
    if args.all:
        targets = [k for k in reg["kbs"] if k.get("sync") == "rebase-5min"]
        # Bases the scheduled sweep does not cover are reported, not dropped: an
        # adopted base is always `manual`, so silence here reads as "everything is
        # synced" when nothing was even looked at.
        for k in reg["kbs"]:
            if k.get("sync") != "rebase-5min":
                print(f"{k.get('name')}: skipped (sync: {k.get('sync')})")
    else:
        base = resolve_base(args)
        targets = [{"name": base.cfg.get("name", base.root.name),
                    "path": str(base.root)}]
    agent = agent_subject(args)
    if args.all and not args.no_jitter and targets:
        time.sleep(sync_jitter())
    worst = 0
    for kb in targets:
        root = Path(kb["path"]).expanduser()
        if not is_repo(root):
            print(f"{kb.get('name')}: skipped (not a git repo)")
            continue
        name = kb.get("name", root.name)
        pid = resolve_principal(args, name, root)
        code = _sync_one(root, name, agent,
                         (principal_name(args, root, pid), pid))
        worst = max(worst, code)
    sys.exit(worst)
