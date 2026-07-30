"""Two identities this tool resolves without ever prompting: the acting AGENT (a
service identity — a harness, a cron, a human at a keyboard) and the human PRINCIPAL
whose knowledge a write belongs to. Also the small git/timestamp/exit helpers every
other module reaches for.

A principal is a human, and git already models this: author = the person whose
knowledge it is, committer = the acting agent. Rebase preserves the author, forges
show it in blame, and no new identity system is invented.

The principal file is a LIST because one person is not one identity — a work address
should not author a personal base. First match wins, so a bare "*" belongs last.
"""

import fnmatch
import os
import re
import subprocess
import sys
import datetime as _dt
from pathlib import Path

import yaml

from .registry import find_household


def now_ts() -> str:
    return _dt.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M%z")[:-2] + ":" + \
        _dt.datetime.now().astimezone().strftime("%z")[-2:]


def today() -> str:
    return _dt.date.today().isoformat()


def die(msg: str, code: int = 1):
    print(f"kb: error: {msg}", file=sys.stderr)
    sys.exit(code)


def agent_subject(args) -> str:
    return getattr(args, "agent", None) or os.environ.get("AOS_AGENT", "agent:main")


def agent_email(subject: str) -> str:
    """A syntactically valid address for an agent subject. The subject itself is the
    committer *name*, so `git log %cn` reads back as the subject with no parsing."""
    local = re.sub(r"[^a-zA-Z0-9._-]+", "-", subject).strip("-").lower() or "agent"
    return f"{local}@agents.local"


def git(root: Path, *argv) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], cwd=root, capture_output=True,
                          text=True, check=False)


def is_repo(root: Path) -> bool:
    return (root / ".git").exists()


SEQUENCER_STATES = ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD",
                    "REVERT_HEAD")


def sequencer_state(root: Path) -> str | None:
    """Any operation left mid-flight. `git status --porcelain=v2` does NOT report
    these — its documented headers are branch.* only — so the state paths are the
    reliable test, which is what git's own git-prompt.sh uses. Staging a worktree in
    this condition commits conflict markers, and git then refuses to start another
    rebase over the old one ("I am stopping in case you still have something
    valuable there"), so the next tick fails forever."""
    for s in SEQUENCER_STATES:
        p = git(root, "rev-parse", "--git-path", s).stdout.strip()
        if p and (root / p).exists():
            return s
    return None


# ---------------------------------------------------------------- principal
WEAK_PRINCIPAL_MARKERS = ("agents@localhost", "noreply@", "@localhost")


def principal_file() -> Path:
    home = find_household()
    return (home / ".aos" / "kb-principal.yml") if home else \
        Path.home() / ".aos" / "kb-principal.yml"


def load_principals() -> list:
    p = principal_file()
    if not p.exists():
        return []
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or []
    return data if isinstance(data, list) else []


def save_principals(entries: list):
    p = principal_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "# The humans this machine writes as. First match wins, so a bare `*` belongs\n"
        "# last. Machine-local and gitignored: `kb` writes it on the first verb call\n"
        "# and kb's ONBOARDING.md fixes what detection got wrong.\n"
        + yaml.safe_dump(entries, sort_keys=False, allow_unicode=True),
        encoding="utf-8")


def synthesize_principal() -> str:
    import getpass
    import socket
    user = re.sub(r"[^a-z0-9._-]+", "-", getpass.getuser().lower()) or "user"
    host = re.sub(r"[^a-z0-9.-]+", "-", socket.gethostname().split(".")[0].lower()) \
        or "localhost"
    return f"{user}@{host}.local"


def is_weak_principal(pid: str) -> bool:
    pid = (pid or "").lower()
    return (not pid) or pid.endswith(".local") \
        or any(m in pid for m in WEAK_PRINCIPAL_MARKERS)


def resolve_principal(args, base_name: str, root: Path = None,
                      persist: bool = True) -> str:
    """$AOS_PRINCIPAL_ID -> first matching file entry -> git config user.email ->
    synthesized. Written once, reused. NEVER prompts and never blocks: this runs
    under a 5-second capture budget and under a cron with no tty. A weak value is
    lint's finding, not an error.

    `persist=False` for the read-only verbs. A report is not a reason to establish an
    identity: `kb lint` on someone else's base would otherwise create
    <home>/.aos/kb-principal.yml as a side effect of reading, which is both a
    surprise and a wrong answer to "whose base is this".
    """
    entries = load_principals()
    env = getattr(args, "principal", None) or os.environ.get("AOS_PRINCIPAL_ID")
    if env and env.strip():
        env = env.strip()
        # Seeded on the way past when there is no file yet: "established on first use"
        # has to mean the first use, whatever supplied the identity. An existing file
        # is left alone — env is an override, and an override that rewrote the file
        # would make itself permanent.
        if persist and not entries:
            save_principals([{"id": env, "bases": ["*"]}])
        return env
    for e in entries:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        for pat in (e.get("bases") or ["*"]):
            if fnmatch.fnmatch(base_name, str(pat)):
                return str(e["id"]).strip()
    pid = ""
    if root is not None:
        pid = git(root, "config", "user.email").stdout.strip()
    if not pid:
        pid = synthesize_principal()
    if persist:
        entries.append({"id": pid, "bases": ["*"]})
        save_principals(entries)
    return pid


def principal_name(args, root: Path, pid: str) -> str:
    """The git author *name* for that principal — cosmetic beside the id, which is the
    thing grants and dedup key on."""
    name = os.environ.get("AOS_PRINCIPAL_NAME", "").strip()
    if not name and root is not None:
        name = git(root, "config", "user.name").stdout.strip()
    return name or (pid or "user").split("@")[0]
