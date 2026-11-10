"""Fill a command template from the sheet and run it — no shell, one token at a time, so a
title or a path with spaces or quotes stays one argument. The first word is replaced by the
recorded absolute CLI, which is what lets a caller with a reduced PATH still reach the harness."""

import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Mapping, Optional

from .constants import LEFTOVER_RE, MARK_TIMEOUT, SKILLS_TOKEN
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


def mark_unread(harness: Harness, profile: str, session_id: str) -> Optional[str]:
    """The sheet's optional `mark_unread` step, on a session this tool just created: a harness may
    count a session nobody opened as read. Never fatal — returns the reason for one warning line,
    else None. A command runs like any other step; an `http` step reads the profile's own key from
    the env file its `env_file` command names, and never prints it."""
    step = harness.session.get("mark_unread")
    if step is None:
        return None
    values = {"<profile>": profile, "<session_id>": session_id}
    try:
        if isinstance(step, str):
            ran = _quiet(harness, argv(harness, step, values))
            return None if ran.returncode == 0 else f"exit {ran.returncode}"
        if isinstance(step, dict) and isinstance(step.get("http"), str):
            return _http(harness, step, values)
    except SystemExit:  # a template `argv` refused; it already said why on stderr
        return "the sheet's mark_unread row is malformed"
    except Exception as e:  # the session exists: no failure here may lose it
        return type(e).__name__
    return "mapping.session.mark_unread is neither a command nor an http step"


def _quiet(harness: Harness, cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          timeout=MARK_TIMEOUT, env=child_env(harness))


def _http(harness: Harness, step: dict, values: Mapping[str, str]) -> Optional[str]:
    name = step.get("key")
    key = _env_value(harness, step.get("env_file"), name, values)
    if not key:
        return f"no {name} in this profile's env file"
    method, _, url = step["http"].partition(" ")
    for placeholder, value in values.items():
        url = url.replace(placeholder, urllib.parse.quote(value, safe=""))
    request = urllib.request.Request(
        url.strip(), method=method, data=json.dumps(step.get("json") or {}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    # The harness's API is local: never route it through the caller's proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=MARK_TIMEOUT):
            return None
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except urllib.error.URLError:
        return f"cannot reach {urllib.parse.urlsplit(url.strip()).netloc}"


def _env_value(harness: Harness, env_file: object, name: object,
               values: Mapping[str, str]) -> Optional[str]:
    """`NAME=value` from the env file the harness names — the last assignment wins, as in a shell."""
    if not isinstance(env_file, str) or not isinstance(name, str):
        return None
    ran = _quiet(harness, argv(harness, env_file, values))
    if ran.returncode != 0 or not ran.stdout.strip():
        return None
    try:
        lines = open(os.path.expanduser(ran.stdout.strip()), encoding="utf-8",
                     errors="replace").read().splitlines()
    except OSError:
        return None
    found = None
    for line in lines:
        k, sep, v = line.strip().removeprefix("export ").partition("=")
        if sep and k.strip() == name:
            found = v.strip().strip("'\"")
    return found or None
