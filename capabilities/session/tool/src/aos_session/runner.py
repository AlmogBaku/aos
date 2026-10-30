"""Fill a command template from the sheet and run it — no shell, one token at a time, so a
title or a path with spaces or quotes stays one argument. The first word is replaced by the
recorded absolute CLI, which is what lets a caller with a reduced PATH still reach the harness."""

import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Mapping, Optional

from .constants import LEFTOVER_RE, SKILLS_TOKEN
from .errors import Exit, fail
from .harness import Harness


@dataclass
class Ran:
    code: int
    stdout: str
    stderr: str


def argv(harness: Harness, template: str, values: Mapping[str, str],
         skills: tuple[str, ...] = ()) -> list[str]:
    if not harness.cli:
        fail(Exit.BAD_INPUT, f"no {harness.name} CLI recorded — run `aos-cap harness set "
                             f"{harness.name}` where the CLI is on PATH")
    tokens = shlex.split(template)
    out = [harness.cli]
    for tok in tokens[1:]:
        if tok == SKILLS_TOKEN:
            skill_arg = harness.session.get("skill_arg")
            if skills and not isinstance(skill_arg, str):
                fail(Exit.BAD_INPUT, f"the {harness.name} cheat-sheet has no "
                                     f"mapping.session.skill_arg for --skills")
            for name in skills:
                out.extend(t.replace("<name>", name) for t in shlex.split(skill_arg))
            continue
        # One pass: a value is never scanned again, so a title like "Review <draft>" stays
        # text instead of failing as an unknown placeholder or having `<file>` filled in.
        out.append(LEFTOVER_RE.sub(lambda m: _fill(harness, values, m.group(0)), tok))
    return out


def _fill(harness: Harness, values: Mapping[str, str], key: str) -> str:
    if key not in values:
        fail(Exit.BAD_INPUT, f"the {harness.name} cheat-sheet template uses an unknown "
                             f"placeholder {key}")
    return values[key]


def child_env(harness: Harness, env: Optional[Mapping[str, str]] = None) -> dict[str, str]:
    """The caller's env minus what the sheet says must not leak into a new session (a cron
    run's identity, for example). `PREFIX*` drops every variable starting with PREFIX."""
    env = dict(os.environ if env is None else env)
    for pat in harness.session.get("scrub_env") or []:
        pat = str(pat)
        if pat.endswith("*"):
            for k in [k for k in env if k.startswith(pat[:-1])]:
                env.pop(k)
        else:
            env.pop(pat, None)
    return env


def run(harness: Harness, cmd: list[str], timeout: float, title: str) -> Ran:
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           timeout=timeout, env=child_env(harness))
    except subprocess.TimeoutExpired:
        print(f'timeout: session "{title}" may still exist', file=sys.stderr)
        sys.exit(Exit.TIMEOUT)
    except OSError as e:
        fail(Exit.HARNESS_FAILED, f"cannot run {cmd[0]}: {e.strerror}")
    return Ran(p.returncode, p.stdout, p.stderr)


def failure(ran: Ran, what: str) -> None:
    """The one failure report: `[CRON_FAILURE]` first, so a cron job's deliver step carries it
    as-is, then the harness exit code and the tail of its stderr."""
    print("[CRON_FAILURE]")
    print(f"{what}: exit {ran.code}")
    tail = [line for line in ran.stderr.splitlines() if line.strip()][-20:]
    if tail:
        print("\n".join(tail))
    sys.exit(Exit.HARNESS_FAILED)
