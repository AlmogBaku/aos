"""aos-cap — the deterministic half of a capability's lifecycle (ARCHITECTURE §2.4).

No judgment anywhere: files, stdout and exit codes are the whole interface. Four
areas of work, which is why the tool is named for the capability and not for the
lockfile — only the last group is lockfile bookkeeping:

  manifest  parse + validate a CAPABILITY.md -> JSON on stdout
  skills    compute each skill's INSTALLED name; --check IS the collision gate
  agents    the same, for the agents it ships — one flat namespace, one exit code
  render    copy one skill to its installed name, resolving its name slots
            (mechanical, idempotent)
  home      print the resolved household root
  init/record/rehash/verify/show/list/remove  own the lockfile
  (<home>/.aos/installs.lock.yaml — the aos household root, e.g. ~/aos)

The lockfile is THIS TOOL'S file: agents call verbs, never edit the YAML.
Exit codes: 0 ok · 1 generic (e.g. init over an existing lockfile) · 12 manifest
invalid · 13 drift · 14 no such entry · 15 no home · 16 artifact missing ·
17 skill-or-agent-name collision · 18 unresolvable {{skill:}}/{{agent:}} slot.
"""

from typing import Optional

import typer

from .commands._shared import GlobalOpts, version_callback
from .commands.inspect import app as inspect_app
from .commands.render import app as render_app
from .commands.lockfile import app as lockfile_app

app = typer.Typer(rich_markup_mode=None, add_completion=False,
                  help="Deterministic lifecycle bookkeeping for aos capabilities: the "
                       "manifest, the installed skill and agent names, the render, and "
                       "the lockfile. See `--help` per verb. "
                       "NOTE: --home is global, so it goes BEFORE the verb "
                       "(`aos-cap --home ~/aos record …`, never `aos-cap record --home …`) "
                       "— the same shape the `kb` tool's --base has.")

app.add_typer(inspect_app)
app.add_typer(render_app)
app.add_typer(lockfile_app)


@app.callback()
def main_callback(
    ctx: typer.Context,
    home: Optional[str] = typer.Option(
        None, "--home", help="household root, e.g. ~/aos (else $AOS_HOME, else a "
                             "cwd-upward .aos/ search)"),
    version: bool = typer.Option(
        False, "--version", callback=version_callback, is_eager=True),
):
    # Deliberately LAZY: never calls find_home() here — only stashes the raw string the
    # user passed. See commands/_shared.py's docstring for why (init must accept a
    # household that does not exist yet; every other verb must reject one).
    ctx.obj = GlobalOpts(home=home)


def main():
    app()


if __name__ == "__main__":
    main()
