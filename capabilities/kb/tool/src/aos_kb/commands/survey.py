"""`import survey` — inventory + shape detection of a foreign source tree. Import
itself is an AGENT procedure (the import skill) — transform-on-import means every
page passes through agent judgment, so there is no apply engine. The tool contributes
exactly one deterministic piece: the survey, so the agent never burns a context
walking a big tree. The source is READ-ONLY, always.

Isolated in its own module because it is the one verb that reads a foreign,
non-kb tree (`args.src`, not `resolve_base()`) and needs its own nested
subcommand (`kb import survey`, with room for a future `kb import <other>`)."""

import fnmatch
import json as _json
from pathlib import Path
from typing import Annotated

import typer

from ..constants import WIKILINK_RE
from ..frontmatter import read_frontmatter
from ..identity import die

app = typer.Typer(help="bulk import of a foreign KB (source is READ-ONLY, always; "
                       "design §6.7)")

IMPORT_SKIP_DEFAULT = ["**/.git/**", "**/.obsidian/**", "**/node_modules/**",
                       "**/.kb/**", "**/*.backup.*", "**/*.bak"]


def _src_files(src: Path, skips):
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src).as_posix()
        if any(fnmatch.fnmatch(rel, s) or fnmatch.fnmatch("/" + rel, s)
               for s in skips):
            continue
        yield rel, p


@app.command("survey", help="inventory + shape detection of a source tree")
def cmd_import_survey(src: str, as_json: Annotated[bool, typer.Option("--json")] = False):
    src = Path(src).expanduser().resolve()
    if not src.is_dir():
        die(f"{src} is not a directory")
    # shape detection
    if (src / ".kb" / "base.yml").exists() or (src / "BASE.yaml").exists():
        shape = "base-native"
    elif (src / "SCHEMA.md").exists() and ((src / "state").is_dir()
                                           or (src / "ops" / "inbox.md").exists()):
        shape = "old-methodology"
    elif (src / ".obsidian").is_dir():
        shape = "obsidian"
    else:
        shape = "plain"

    by_dir, by_ext, fm_fields = {}, {}, {}
    links = md = big = 0
    big_files = []
    for rel, p in _src_files(src, IMPORT_SKIP_DEFAULT):
        top = rel.split("/")[0] if "/" in rel else "."
        by_dir[top] = by_dir.get(top, 0) + 1
        ext = p.suffix or "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1
        if p.suffix == ".md":
            md += 1
            fm, body = read_frontmatter(p)
            for k in (fm or {}):
                fm_fields[k] = fm_fields.get(k, 0) + 1
            links += len(WIKILINK_RE.findall(body))
        elif p.stat().st_size > 1024 * 1024:
            big += 1
            big_files.append(rel)

    if as_json:
        print(_json.dumps({"shape": shape, "by_dir": by_dir, "by_ext": by_ext,
                          "md_files": md, "wikilinks": links,
                          "frontmatter_fields": fm_fields,
                          "large_binaries": big_files}, indent=2))
        return
    print(f"# import survey — {src}\n")
    print(f"shape: {shape}"
          + ("  (already a base — use `kb adopt`, not import)"
             if shape == "base-native" else ""))
    print(f"markdown files: {md} · wikilinks: {links} · large binaries: {big}")
    print("\nby top-level dir:")
    for d, n in sorted(by_dir.items(), key=lambda x: -x[1]):
        print(f"  {d:24} {n}")
    print("\nfrontmatter fields seen (count):")
    for k, n in sorted(fm_fields.items(), key=lambda x: -x[1]):
        print(f"  {k:24} {n}")
    if big_files:
        print("\nlarge binaries (candidates for LFS-tracked attachment sets):")
        for rel in big_files[:20]:
            print(f"  {rel}")
