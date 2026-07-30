"""kb — the kb capability's deterministic executor.

Deterministic operations ONLY: this tool never calls an LLM and never invokes an
agent. Skills call it; it answers in exit codes, stdout, and files — files are the
async message bus (a sync conflict becomes a .kb/pending/ entry, not a
callback). Every write verb makes its own commit: author = the human principal whose
knowledge it is, committer = the acting agent, with aos-verb/aos-path trailers. Git is
the single audit substrate — there is no log.md.

Every shared record is one file per record (captures, pending entries, per-principal
state). That is what keeps a base conflict-free when several machines — or
several people — sync it; nothing here relies on a merge driver.

Reports (lint, adopt) are report-only and written for an LLM to judge: the report is
the interface. Search/links exit codes carry no information beyond "ran".

Layout guard: every base-scoped verb validates .kb/base.yml `layout` and fails loudly
on mismatch — never path-guesses across format generations. A layout 1 tree (root
BASE.yaml) is recognised only to point at `kb migrate`.

Spec: design/kb-methodology.md (spec branch). Contract = verb set + boundary; the
implementation language is a build choice.
"""

from typing import Optional

import typer

from .commands._shared import GlobalOpts, version_callback
from .commands.lifecycle import app as lifecycle_app
from .commands.capture import app as capture_app, pending_app
from .commands.wiki import app as wiki_app
from .commands.lint import app as lint_app
from .commands.sync import app as sync_app
from .commands.admin import app as admin_app
from .commands.survey import app as survey_app

app = typer.Typer(rich_markup_mode=None, add_completion=False,
                  help="Deterministic executor for kb bases. Judgment-free: skills "
                       "decide, this tool does. See `--help` per verb.")

app.add_typer(lifecycle_app)
app.add_typer(capture_app)
app.add_typer(pending_app, name="pending",
             help="the one queue: add | list | resolve")
app.add_typer(wiki_app)
app.add_typer(lint_app)
app.add_typer(sync_app)
app.add_typer(admin_app)
app.add_typer(survey_app, name="import")


@app.callback()
def main_callback(
    ctx: typer.Context,
    base: Optional[str] = typer.Option(
        None, "--base", help="base name (registry) or path; default: cwd/registry "
                            "default"),
    registry: Optional[str] = typer.Option(
        None, "--registry",
        help="kb-registry.yaml path (default: <home>/personal/kb-registry.yaml)"),
    agent: Optional[str] = typer.Option(
        None, "--agent", help="acting subject — the committer of every write "
                             "(default $AOS_AGENT or agent:main)"),
    principal: Optional[str] = typer.Option(
        None, "--principal",
        help="the human a write belongs to; becomes the git author and the grants "
             "subject (default $AOS_PRINCIPAL_ID, else the first matching entry in "
             "<home>/.aos/kb-principal.yml, else the repo's git identity). The "
             "display name rides $AOS_PRINCIPAL_NAME"),
    version: bool = typer.Option(
        False, "--version", callback=version_callback, is_eager=True),
):
    # Deliberately LAZY: never calls Base() or resolve_principal() here — only
    # stashes the raw strings the user passed. See commands/_shared.py's docstring
    # for why (migrate's layout-1 tolerance depends on this).
    ctx.obj = GlobalOpts(base=base, registry=registry, agent=agent,
                        principal=principal)


def main():
    app()


if __name__ == "__main__":
    main()
