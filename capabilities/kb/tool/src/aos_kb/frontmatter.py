"""Reading and writing a page's `---`-delimited YAML block, plus the git-style glob
matcher grants rows use. Both parsers deliberately tolerant: a page with malformed
frontmatter is a lint finding, not a crash."""

import re
import unicodedata
from pathlib import Path

import yaml


def slugify(text: str, max_len: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].strip("-") or "item"


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.S)


def read_frontmatter(path: Path):
    """Return (frontmatter dict or None, body str). Tolerant: bad YAML -> None.
    One parser for both halves: the same regex bounds the fm block and the body."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None, ""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, text
    if not isinstance(fm, dict):
        return None, text
    return fm, text[m.end():]


def write_frontmatter(path: Path, fm: dict, body: str):
    front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{front}\n---\n{body}", encoding="utf-8")


def glob_to_re(pattern: str) -> re.Pattern:
    """git-style glob: ** crosses /, * does not."""
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if pattern[i:i + 2] == "**":
                i += 2
                if i < len(pattern) and pattern[i] == "/":
                    i += 1
                    out.append("(?:.*/)?")   # any depth, but never a name suffix
                else:
                    out.append(".*")
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")
