"""Two identities this tool resolves without ever prompting: the acting AGENT (a
service identity — a harness, a cron, a human at a keyboard) and the human PRINCIPAL
whose knowledge a write belongs to. Also the small git/timestamp/exit helpers every
other module reaches for.

A principal is a human, and git already models this: author = the person whose
knowledge it is, committer = the acting agent. Rebase preserves the author, forges
show it in blame, and no new identity system is invented.

The principal is `--principal`/$AOS_PRINCIPAL_ID, else the first matching entry in
<home>/.aos/kb-principal.yml — never guessed. The file is a LIST because one person is
not one identity — a work address should not author a personal base. First match wins,
so a bare "*" belongs last. `kb init` fills in a MISSING identity, from the flag typed
on it, and `kb config set principal.id=` changes it; an override is never saved.
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
    return find_household() / ".aos" / "kb-principal.yml"


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
        "# last. Machine-local and gitignored: `kb init --principal <id>` fills it in\n"
        "# when missing, `kb config set principal.id=<id>` changes it.\n"
        + yaml.safe_dump(entries, sort_keys=False, allow_unicode=True),
        encoding="utf-8")


def is_weak_principal(pid: str) -> bool:
    pid = (pid or "").lower()
    return (not pid) or pid.endswith(".local") \
        or any(m in pid for m in WEAK_PRINCIPAL_MARKERS)


def override_principal(args) -> str | None:
    """`--principal`, else $AOS_PRINCIPAL_ID: used for this call, never written."""
    pid = getattr(args, "principal", None) or os.environ.get("AOS_PRINCIPAL_ID")
    return pid.strip() if pid and pid.strip() else None


def typed_principal(args) -> str | None:
    """`--principal` alone: what was typed on this command, not what a shell exports."""
    pid = getattr(args, "principal", None)
    return pid.strip() if pid and pid.strip() else None


def file_principal(base_name: str, entries: list | None = None) -> str | None:
    """The first entry in the principal file whose `bases` globs match."""
    for e in (load_principals() if entries is None else entries):
        if not isinstance(e, dict) or not str(e.get("id") or "").strip():
            continue
        for pat in (e.get("bases") or ["*"]):
            if fnmatch.fnmatch(base_name, str(pat)):
                return str(e["id"]).strip()
    return None


def no_principal(base_name: str):
    die(f"no principal for base {base_name!r}: no --principal, no $AOS_PRINCIPAL_ID, "
        f"and no matching entry in {principal_file()}. Set one with "
        f"`kb config set principal.id=<id>` (on a fresh machine, "
        f"`kb init --principal <id>`); or pass --principal / set AOS_PRINCIPAL_ID "
        f"for one call")


def resolve_principal(args, base_name: str, required: bool = True) -> str | None:
    """The override -> the first matching file entry -> nothing. Never guessed and never
    prompted for: this runs under a 5-second capture budget and under a cron with no tty.
    A guess (git's user.email, a synthesized user@host) authors writes as whoever the
    machine happens to say, so a write with no identity is an error naming the file.

    `required=False` for the read-only verbs, which run with no identity at all (None):
    `kb lint` on someone else's base has no business needing one."""
    pid = override_principal(args) or file_principal(base_name)
    if pid is None and required:
        no_principal(base_name)
    return pid


def init_principal(args, base_name: str) -> tuple[str, bool]:
    """`kb init`'s identity, and whether init saves it — the one write an identity ever
    gets outside `kb config set`. Only when there is NO identity at all, and only the
    typed `--principal`: $AOS_PRINCIPAL_ID is whatever a shell exports, and saving it
    would make that the permanent author. With any entry on file, the file is left alone
    and a typed flag is this call's override, as on every other verb."""
    entries = [e for e in load_principals()
               if isinstance(e, dict) and str(e.get("id") or "").strip()]
    typed = typed_principal(args)
    if not entries:
        if typed is None:
            die(f"no identity in {principal_file()} — run "
                f"`kb config set principal.id=<you>` (or, on a fresh machine, "
                f"`kb init --principal <you>`). $AOS_PRINCIPAL_ID is a per-call "
                f"override and is never saved")
        return typed, True
    if typed and typed != file_principal(base_name, entries):
        print(f"note: --principal {typed} authors this init only — the saved identity "
              f"in {principal_file()} was left unchanged (change it with "
              f"`kb config set principal.id=<id>`).")
    return resolve_principal(args, base_name), False


def principal_name(args, root: Path, pid: str) -> str:
    """The git author *name* for that principal — cosmetic beside the id, which is the
    thing grants and dedup key on."""
    name = os.environ.get("AOS_PRINCIPAL_NAME", "").strip()
    if not name and root is not None:
        name = git(root, "config", "user.name").stdout.strip()
    return name or (pid or "user").split("@")[0]
