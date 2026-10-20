"""aos-session — open one new titled session, or add a turn to the session that asked.

Two commands, harness-free: the household's `.aos/harness.yml` names the installed cheat-sheet,
and its frontmatter `mapping.session` supplies the command templates. No fallback of its own —
a failure exits non-zero with the reason, and the caller decides what follows.

  open    one new titled session with an opening prompt; the title ends with the local time,
          because a harness may reopen a title that exists
  notify  continue a known session — waiting while the harness reports it busy — and open a
          new one only when the harness reports it gone

Exit codes: 0 ok · 1 the harness command failed · 2 bad input, no household or no harness
record · 4 not supported on this harness · 124 timeout.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer

from . import harness as hz
from . import runner
from .constants import BUSY_RETRY, BUSY_WAIT, DEFAULT_TIMEOUT, ID_RE, TITLE_MAX, VERSION
from .errors import Exit, fail

app = typer.Typer(rich_markup_mode=None, add_completion=False, help=__doc__.split("\n\n")[0])


def _version(value: bool) -> None:
    if value:
        typer.echo(f"aos-session {VERSION}")
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    home: Annotated[Optional[str], typer.Option(
        "--home", help="household root (else $AOS_HOME, else ~/aos)")] = None,
    version: Annotated[bool, typer.Option(
        "--version", callback=_version, is_eager=True, help="print the version")] = False,
) -> None:
    ctx.obj = home


def _check_id(flag: str, value: str) -> None:
    if not ID_RE.match(value):
        fail(Exit.BAD_INPUT, f"{flag} '{value}' must match {ID_RE.pattern}")


def _prompt(path: str) -> str:
    p = Path(path).expanduser()
    if not p.is_file():
        fail(Exit.BAD_INPUT, f"--prompt-file {path} is not a file")
    return str(p.resolve())


def _titled(title: str) -> str:
    title = " ".join(title.split())
    if not title:
        fail(Exit.BAD_INPUT, "--title is empty")
    if "#" in title:
        fail(Exit.BAD_INPUT, "--title must not carry '#' (a harness may read it as a lineage)")
    suffix = datetime.now().strftime(" %H:%M")
    return title[:TITLE_MAX - len(suffix)].rstrip() + suffix


def _open(h: hz.Harness, profile: str, title: str, prompt: str, workdir: str,
          skills: tuple[str, ...], timeout: float) -> tuple[str, str]:
    """Run the sheet's `open` step; print nothing, return (new session id, harness stdout)."""
    cmd = runner.argv(h, hz.step(h, "open"),
                      {"<profile>": profile, "<title>": title, "<file>": prompt,
                       "<workdir>": workdir}, skills)
    ran = runner.run(h, cmd, timeout, title)
    if ran.code != 0:
        runner.failure(ran, f'open "{title}"')
    ids = hz.pattern(h, "id").findall(ran.stderr)
    if not ids:
        ran.code = ran.code or 1
        runner.failure(ran, f'open "{title}" printed no session id')
    return ids[-1], ran.stdout


@app.command("open", help="open one new titled session seeded with a prompt file")
def cmd_open(
    ctx: typer.Context,
    profile: Annotated[str, typer.Option("--profile", help="the agent (harness profile) to open it in")],
    title: Annotated[str, typer.Option("--title", help="the title; the local time is appended")],
    prompt_file: Annotated[str, typer.Option("--prompt-file", help="the opening prompt")],
    workdir: Annotated[Optional[str], typer.Option("--workdir", help="default: the current dir")] = None,
    skill: Annotated[Optional[list[str]], typer.Option("--skills", help="repeatable: a skill to preload")] = None,
    timeout: Annotated[float, typer.Option("--timeout", help="seconds")] = DEFAULT_TIMEOUT,
) -> None:
    _check_id("--profile", profile)
    h = hz.load(hz.find_home(ctx.obj))
    titled = _titled(title)
    sid, stdout = _open(h, profile, titled, _prompt(prompt_file), workdir or str(Path.cwd()),
                        tuple(skill or ()), timeout)
    print(f'Opened "{titled}" (session {sid}) in profile {profile}.')
    if stdout.strip():
        print()
        print(stdout.rstrip())


@app.command("notify", help="add a turn to a known session; open a new one only if it is gone")
def cmd_notify(
    ctx: typer.Context,
    profile: Annotated[str, typer.Option("--profile", help="the agent (harness profile) of the session")],
    session: Annotated[str, typer.Option("--session", help="the session id to continue")],
    prompt_file: Annotated[str, typer.Option("--prompt-file", help="the turn to add")],
    title: Annotated[str, typer.Option("--title", help="title for a new session if this one is gone")],
    workdir: Annotated[Optional[str], typer.Option("--workdir", help="default: the current dir")] = None,
    timeout: Annotated[float, typer.Option("--timeout", help="seconds")] = DEFAULT_TIMEOUT,
) -> None:
    _check_id("--profile", profile)
    _check_id("--session", session)
    h = hz.load(hz.find_home(ctx.obj))
    prompt = _prompt(prompt_file)
    cmd = runner.argv(h, hz.step(h, "continue"),
                      {"<profile>": profile, "<session_id>": session, "<file>": prompt,
                       "<workdir>": workdir or str(Path.cwd())})
    busy = hz.pattern(h, "busy") if "busy" in h.session else None
    deadline = time.monotonic() + BUSY_WAIT
    while True:
        ran = runner.run(h, cmd, timeout, session)
        waiting = ran.code != 0 and busy is not None and bool(busy.search(ran.stderr))
        if not waiting or time.monotonic() >= deadline:
            break
        time.sleep(BUSY_RETRY)
    if ran.code == 0:
        print(f"Added to session {session} in profile {profile}.")
        if ran.stdout.strip():
            print()
            print(ran.stdout.rstrip())
        return
    if waiting:
        runner.failure(ran, f"continue {session}: still busy after {BUSY_WAIT:.0f}s")
    if not hz.pattern(h, "missing").search(ran.stderr):
        runner.failure(ran, f"continue {session}")
    titled = _titled(title)
    sid, stdout = _open(h, profile, titled, prompt, workdir or str(Path.cwd()), (), timeout)
    print(f'Session {session} is gone; opened "{titled}" (session {sid}) in profile {profile}.')
    if stdout.strip():
        print()
        print(stdout.rstrip())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
