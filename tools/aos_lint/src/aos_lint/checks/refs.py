import os
import re
from urllib.parse import unquote

from ..frontmatter import read_frontmatter, strip_code_fences

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_SCHEME = re.compile(r"^(https?:|mailto:|#)")

# Every relative markdown link in the repo must resolve — the reading order,
# capability cross-links, and design exhibits are all load-bearing.
# Methodology init/ files are templates — their links resolve inside the
# scaffolded KB, not inside this repo.
TEMPLATE_RE = re.compile(r"/methodologies/[^/]+/init/")


def check_references(ctx) -> None:
    root = str(ctx.root)
    for rel in ctx.files:
        if not rel.endswith(".md") or TEMPLATE_RE.search(rel):
            continue
        abs_path = ctx.root / rel
        parsed = read_frontmatter(abs_path)
        text = strip_code_fences(parsed.body)
        for match in LINK_RE.finditer(text):
            target = match.group(1)
            if _SCHEME.match(target):
                continue
            target = target.split("#")[0]
            if not target:
                continue
            resolved = os.path.normpath(
                os.path.join(os.path.dirname(str(abs_path)), unquote(target)))
            if not resolved.startswith(root.rstrip("/\\") + os.sep):
                ctx.report("error", "refs/escape", rel,
                           f'link "{match.group(1)}" points outside the repo')
            elif not os.path.exists(resolved):
                ctx.report("error", "refs/dead", rel,
                           f'link "{match.group(1)}" does not resolve')
