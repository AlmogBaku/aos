"""Reading a `---`-delimited YAML frontmatter block, in the shape the LINT needs.

Deliberately not `aos_cap.frontmatter`: that pair is the shipped tool's (one exits 12 on a
malformed manifest, the other returns None), and a linter must do neither — it has to
REPORT the parse error against the file, with the message, and keep going to the next
capability. So this returns the error rather than acting on it."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Parsed:
    data: Optional[dict]
    body: str
    error: Optional[str]


def read_frontmatter(path) -> Parsed:
    """`data` is None when there is no frontmatter, and `error` carries a message when the
    block exists but does not parse."""
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return Parsed(None, text, None)
    end = text.find("\n---", 3)
    if end == -1:
        return Parsed(None, text, "unterminated frontmatter block")
    raw = text[text.find("\n") + 1:end]
    nl = text.find("\n", end + 1)
    body = text[nl + 1:] if nl != -1 else ""
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return Parsed(None, body, str(e))
    if data is not None and not isinstance(data, dict):
        return Parsed(None, body, "frontmatter is not a YAML mapping")
    return Parsed(data if data is not None else {}, body, None)


_FENCE = None


def strip_code_fences(markdown: str) -> str:
    """Strip fenced code blocks so link/pattern scans don't trip on examples."""
    global _FENCE
    if _FENCE is None:
        import re
        # /^(```|~~~).*?^\1[^\S\n]*$/gms — the closing fence must be the SAME marker, so a
        # ``` block containing ~~~ is one block, not two.
        _FENCE = re.compile(r"^(```|~~~).*?^\1[^\S\n]*$", re.S | re.M)
    return _FENCE.sub("", markdown)
