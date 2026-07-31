"""Reading a YAML frontmatter block, in the two flavours this tool needs: the hard one
that exits 12 on anything malformed (the manifest under validation), and the soft one
that returns None (a neighbour capability or a stranger's skill, which must not be able
to abort somebody else's install)."""

import re
from pathlib import Path
from typing import Optional

import yaml

from .errors import Exit, fail


def frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(Exit.MANIFEST_INVALID, f"{path}: no YAML frontmatter block")
    m = re.search(r"^---\s*$", text[4:], flags=re.M)
    if not m:
        fail(Exit.MANIFEST_INVALID, f"{path}: unterminated frontmatter block")
    end = 4 + m.start()
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as e:
        fail(Exit.MANIFEST_INVALID, f"{path}: frontmatter is not valid YAML: {e}")
    if not isinstance(data, dict):
        fail(Exit.MANIFEST_INVALID, f"{path}: frontmatter must be a YAML mapping")
    return data


def frontmatter_soft(path: Path) -> Optional[dict]:
    """Like frontmatter() but returns None instead of exiting — a malformed neighbour
    capability must not block an unrelated install's collision check."""
    try:
        text = path.read_text()
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    m = re.search(r"^---\s*$", text[4:], flags=re.M)
    if not m:
        return None
    try:
        data = yaml.safe_load(text[4:4 + m.start()]) or {}
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None
