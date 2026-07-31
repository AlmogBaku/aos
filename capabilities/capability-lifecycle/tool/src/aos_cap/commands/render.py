"""`render` — the one verb that materializes a skill: copy `skills/<id>/` to
`<out>/<installed-name>/` and stamp the render's frontmatter. Mechanical and idempotent;
the only judgment anywhere near it is the caller's choice of `--out`, which is exactly
why most of this module is the guard that rejects a destination inside the package."""

import re
import shutil
from pathlib import Path
from typing import Annotated

import typer
import yaml

from ..constants import LEGACY_ORIGIN_KEY
from ..errors import Exit, fail
from ..manifest import skill_rows

app = typer.Typer()


def stamp_render(path: Path, name: str, origin: str) -> None:
    """Rewrite the render's frontmatter `name` to the installed name and stamp origin.

    Parses and re-emits the frontmatter rather than editing lines. The stamp lives at
    `metadata.aos.origin` — inside the Agent Skills spec's own extension hatch, because
    SKILL.md is somebody else's schema and we are the vendor in it. That makes the write a
    MERGE: `metadata.<harness>.*` is legitimate sibling data a line-based writer could not
    see, so appending a key would leave a stale nested one intact and clobber nothing it
    meant to. Losing comment and key-order fidelity is acceptable here and nowhere else:
    this runs on a render, which is a generated artifact.
    """
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(Exit.MANIFEST_INVALID, f"{path}: no YAML frontmatter block")
    m = re.search(r"^---\s*$", text[4:], flags=re.M)
    if m is None:
        fail(Exit.MANIFEST_INVALID, f"{path}: unterminated frontmatter block")
    end = 4 + m.start()
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as e:
        fail(Exit.MANIFEST_INVALID, f"{path}: frontmatter is not valid YAML: {e}")
    if not isinstance(data, dict):
        fail(Exit.MANIFEST_INVALID, f"{path}: frontmatter must be a YAML mapping")
    if "name" not in data:
        fail(Exit.MANIFEST_INVALID, f"{path}: frontmatter has no name: field")

    data["name"] = name
    data.pop(LEGACY_ORIGIN_KEY, None)     # never inherit a stale top-level tag
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    aos = meta.get("aos")
    if not isinstance(aos, dict):
        aos = {}
    aos["origin"] = origin                # ours to overwrite; siblings are not
    meta["aos"] = aos
    data["metadata"] = meta

    body = text[end + len(m.group(0)):].lstrip("\n")
    fm = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)
    path.write_text(f"---\n{fm}---\n{body}")


@app.command("render", help="copy one skill to its installed name (idempotent)")
def cmd_render(
    dir: Annotated[str, typer.Argument(help="capability directory")],
    skill: Annotated[str, typer.Argument(help="capability-local skill id")],
    out: Annotated[str, typer.Option(
        "--out", help="parent dir for the render (…/skills)")],
    force: Annotated[bool, typer.Option(
        "--force", help="re-render over an existing render")] = False,
) -> None:
    cap_dir = Path(dir).resolve()
    data, rows = skill_rows(cap_dir)
    row = next((r for r in rows if r["id"] == skill), None)
    if row is None:
        fail(Exit.NO_ENTRY, f"{cap_dir.name}: no declared skill '{skill}'")
    src = cap_dir / "skills" / skill
    dest = Path(out).expanduser() / row["installed_name"]
    # `--out` must never point inside the package being rendered. Two distinct failures
    # live here, and a capability that `capability-build` or `capability-import` wrote hits
    # them on its FIRST upgrade, because it lives in `personal/capabilities/<id>/` — which
    # is exactly where install and upgrade say to render:
    #
    #   1. DATA LOSS, when dest lands on the source itself (the entry skill, whose id
    #      equals the capability's, so `installed_name == skill`). The rmtree below
    #      runs before the copytree, so the user's hand-written skill and its whole
    #      reference/ tree are deleted and then the copy dies on what it just removed.
    #   2. A BRICKED MANIFEST, when dest lands elsewhere under the package's `skills/`
    #      (any non-entry skill: `skills/drain` renders to `skills/<prefix>drain`). That
    #      is a second on-disk skill nothing declares, so every later `manifest`, `skills`
    #      and `render` on the capability fails exit 12 — and the install that created it
    #      can no longer be upgraded or removed.
    #
    # Rejecting the whole package directory covers both, and is what the skills mean by
    # "render into the household's skills root": somewhere outside the package.
    src_r, dest_r, pkg_r = src.resolve(), dest.resolve(), cap_dir.resolve()
    if dest_r == pkg_r or pkg_r in dest_r.parents:
        fail(Exit.GENERIC,
             f"--out points inside the package being rendered ({dest}) — that would "
             f"{'delete the source' if dest_r == src_r else 'add an undeclared skill the manifest then rejects'}. "
             f"Render to a destination outside {cap_dir}.")
    if dest.is_symlink():
        # A link where the render belongs is someone else's artifact, not ours to rmtree.
        fail(Exit.GENERIC,
             f"{dest} is a symlink — remove it first (renders are real directories)")
    if dest.exists() and not dest.is_dir():
        fail(Exit.GENERIC, f"{dest} exists and is not a directory")
    if dest.is_dir() and any(dest.iterdir()) and not force:
        fail(Exit.GENERIC, f"{dest} exists and is not empty (pass --force to re-render in place)")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    stamp_render(dest / "SKILL.md", row["installed_name"],
                 f"{cap_dir.name}@{data.get('version')}")
    print(f"rendered {cap_dir.name}:{skill} -> {dest}")
