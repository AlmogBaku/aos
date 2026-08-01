"""The four read-only verbs: `manifest` (validate a package, emit it as JSON), `skills`
and `agents` (compute every installed name, and with --check BE the collision gate for
that namespace), `home` (print the resolved household root). Grouped because none of them
writes anything — the worst a caller gets is a report and a non-zero exit."""

import json as jsonlib
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from ..errors import Exit, fail
from ..household import find_home
from ..manifest import agent_rows, skill_rows, validated_manifest
from ..names import agent_collisions, effective_prefix, skill_collisions

app = typer.Typer()


@app.command("manifest", help="parse + validate a CAPABILITY.md -> JSON")
def cmd_manifest(
    dir: Annotated[str, typer.Argument(help="capability directory")],
) -> None:
    jsonlib.dump(validated_manifest(Path(dir)), sys.stdout, indent=2, default=str)
    print()


@app.command("skills", help="each skill's installed name; --check gates collisions (17)")
def cmd_skills(
    ctx: typer.Context,
    dir: Annotated[str, typer.Argument(help="capability directory")],
    check: Annotated[bool, typer.Option(
        "--check", help="fail (17) if any installed name is already claimed")] = False,
    harness_skills: Annotated[Optional[list[str]], typer.Option(
        "--harness-skills", metavar="DIR",
        help="repeatable: a skills directory the harness already reads")] = None,
    json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    harness_skills = list(harness_skills or [])
    cap_dir = Path(dir).resolve()
    data, rows = skill_rows(cap_dir)
    if check:
        collisions, sources = skill_collisions(ctx.obj, harness_skills, cap_dir.name,
                                               rows, cap_dir)
        if collisions:
            for line in collisions:
                print(line, file=sys.stderr)
            fail(Exit.NAME_COLLISION,
                 f"{cap_dir.name}: {len(collisions)} skill-name collision(s) — "
                 f"resolve upstream, never rename at install time")
    if json:
        jsonlib.dump({"capability": cap_dir.name,
                      "skill_prefix": effective_prefix(data, cap_dir.name),
                      "skills": rows}, sys.stdout, indent=2)
        print()
    else:
        for r in rows:
            print(f"{r['id']}\t{r['installed_name']}\t{','.join(r['used_by'])}")
    if check:
        print(f"clean: {len(rows)} skill name{'' if len(rows) == 1 else 's'} unclaimed")
        for s in sources:
            print(f"  checked: {s}")


@app.command("agents", help="each agent's installed name; --check gates collisions (17)")
def cmd_agents(
    ctx: typer.Context,
    dir: Annotated[str, typer.Argument(help="capability directory")],
    check: Annotated[bool, typer.Option(
        "--check", help="fail (17) if any installed name is already claimed")] = False,
    json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Agents land in a flat per-harness namespace exactly like skills — two capabilities
    shipping `archiver` silently override each other — so the identity is the COMPUTED
    `<skill_prefix><agent-id>`, and `--check` is the same single-owner gate under the same
    exit code (17: one code for one hazard, whichever namespace it lands in).

    No `--harness-agents`: enumerating the agents already in the harness is deferred (it
    needs a listing command per cheat-sheet). The `checked:` lines say so — see
    `agent_collisions`."""
    cap_dir = Path(dir).resolve()
    data, rows = agent_rows(cap_dir)
    if check:
        collisions, sources = agent_collisions(ctx.obj, cap_dir.name, rows, cap_dir)
        if collisions:
            for line in collisions:
                print(line, file=sys.stderr)
            fail(Exit.NAME_COLLISION,
                 f"{cap_dir.name}: {len(collisions)} agent-name collision(s) — "
                 f"resolve upstream, never rename at install time")
    if json:
        jsonlib.dump({"capability": cap_dir.name,
                      "skill_prefix": effective_prefix(data, cap_dir.name),
                      "agents": rows}, sys.stdout, indent=2)
        print()
    else:
        for r in rows:
            print(f"{r['id']}\t{r['installed_name']}")
    if check:
        print(f"clean: {len(rows)} agent name{'' if len(rows) == 1 else 's'} unclaimed")
        for s in sources:
            print(f"  checked: {s}")


@app.command("home", help="print the resolved household root (exit 15 if none)")
def cmd_home(ctx: typer.Context) -> None:
    print(find_home(ctx.obj))
