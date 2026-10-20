"""`harness` — record which harness this household installs into, once.

`<aos_home>/.aos/harness.yml` is machine-local state written only through this tool (§3.1).
Two readers: `render`, which ships only that harness's cheat-sheet in the lifecycle skill,
and `aos-session`, which reads `mapping.session` from the recorded `sheet` and runs the
recorded `cli` — an absolute path, so a caller with a reduced PATH (a desktop hook) still
reaches the harness. The `cli` is resolved here, from the first word of the kit sheet's
`mapping.session.open`; a harness CLI that moves is fixed by running `harness set` again."""

import re
import shlex
import shutil
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from ..constants import HARNESS_REL
from ..errors import Exit, fail
from ..frontmatter import frontmatter_soft
from ..household import find_home

app = typer.Typer()
harness_app = typer.Typer(help="record or show the harness this household runs on")
app.add_typer(harness_app, name="harness")

RUNTIME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SHEET_REL = Path("capabilities/capability-lifecycle/skills/capability-lifecycle/reference")


def harness_record(home: Path) -> Optional[dict]:
    """The parsed `.aos/harness.yml`, or None when absent or not a mapping."""
    p = home / HARNESS_REL
    try:
        data = yaml.safe_load(p.read_text())
    except (OSError, yaml.YAMLError):
        return None
    return data if isinstance(data, dict) and data.get("harness") else None


def _cli_from(sheet: Path) -> Optional[str]:
    fm = frontmatter_soft(sheet) or {}
    session = ((fm.get("mapping") or {}).get("session") or {})
    template = session.get("open") if isinstance(session, dict) else None
    if not isinstance(template, str) or not template.strip():
        return None
    first = shlex.split(template)[0]
    return shutil.which(first)


@harness_app.command("set", help="record the harness runtime (writes <aos_home>/.aos/harness.yml)")
def cmd_set(
    ctx: typer.Context,
    runtime: Annotated[str, typer.Argument(help="harness runtime id, e.g. hermes")],
    source: Annotated[Optional[str], typer.Option(
        "--source", help="the kit cheat-sheet to read (default: <aos_home>/upstream/…)")] = None,
    sheet: Annotated[Optional[str], typer.Option(
        "--sheet", help="the installed sheet aos-session reads (default: the lifecycle render)")] = None,
) -> None:
    home = find_home(ctx.obj)
    if not RUNTIME_RE.match(runtime):
        fail(Exit.GENERIC, f"'{runtime}' is not a harness runtime id (lowercase-hyphen)")
    name = f"harness-{runtime}.md"
    src = Path(source).expanduser() if source else home / "upstream" / SHEET_REL / name
    installed = Path(sheet).expanduser() if sheet else home / "personal" / SHEET_REL / name
    cli = _cli_from(src) if src.is_file() else None
    record = {"harness": runtime, "sheet": str(installed), "cli": cli}
    (home / HARNESS_REL).write_text(yaml.safe_dump(record, sort_keys=False))
    print(f"harness: {runtime}")
    if not src.is_file():
        print(f"note: no kit cheat-sheet at {src} — the installer follows no-cheatsheet.md")
    elif cli is None:
        print("note: no harness CLI resolved from mapping.session.open — aos-session cannot "
              "run here until `aos-cap harness set` finds it on PATH")


@harness_app.command("show", help="print the recorded harness (exit 20 if none)")
def cmd_show(ctx: typer.Context) -> None:
    home = find_home(ctx.obj)
    record = harness_record(home)
    if record is None:
        fail(Exit.NO_HARNESS, f"no harness recorded at {home / HARNESS_REL} — run "
                              f"`aos-cap harness set <runtime>`")
    print(yaml.safe_dump(record, sort_keys=False), end="")
