"""The `--where`/`--without` query language every fetch verb speaks.

Generic over frontmatter on purpose: kb does not need to know a field to filter on
it, which is what lets work-tracker own `due:` while `--where due<today+3d` still
works. Date arithmetic lives HERE rather than in a prompt — an LLM computing
"7 days before 2026-08-03" gets it wrong silently.
"""

import re
import datetime as _dt
from typing import Annotated

import typer

from .identity import die

# Every fetch verb takes the same two flags — deterministic filtering by metadata on
# ALL fetch methods, not just inbox. One shared Annotated alias, not one definition
# per verb: `find`, `inbox`, `pending list`, `search`, `links`, `state show` all
# declare `where: WhereOpt = []` and call `parse_where(where)` themselves.
WhereOpt = Annotated[list[str], typer.Option(
    "--where", metavar="key<op>value",
    help="repeatable; dotted paths; ops < <= > >= = ; relative dates today[+-]N[d|w]")]
WithoutOpt = Annotated[list[str], typer.Option(
    "--without", metavar="key", help="the field is absent")]

OPS = ("<=", ">=", "<", ">", "=")
REL_RE = re.compile(r"^today(?:([+-])(\d+)([dw]))?$")


def resolve_date(token: str):
    """`today`, `today+7d`, `today-2w` -> a date. Anything else -> None."""
    m = REL_RE.match(token.strip())
    if not m:
        return None
    sign, n, unit = m.groups()
    if not sign:
        return _dt.date.today()
    days = int(n) * (7 if unit == "w" else 1)
    return _dt.date.today() + _dt.timedelta(days=days if sign == "+" else -days)


def parse_where(exprs) -> list:
    out = []
    for raw in exprs or []:
        for op in OPS:                      # longest first: <= before <
            i = raw.find(op)
            if i > 0:
                key, val = raw[:i].strip(), raw[i + len(op):].strip()
                if not key or not val or any(o in val for o in ("<", ">", "=")):
                    die(f"--where {raw!r} doesn't parse as key<op>value "
                        f"(ops: {' '.join(OPS)})")
                if val.startswith("today") and resolve_date(val) is None:
                    die(f"--where {raw!r}: relative dates are today[+-]N[d|w]")
                out.append((key, op, val))
                break
        else:
            die(f"--where {raw!r} doesn't parse as key<op>value "
                f"(ops: {' '.join(OPS)})")
    return out


def fm_get(fm: dict, dotted: str):
    """Dotted paths reach nested frontmatter (meta.status)."""
    cur = fm
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _coerce(a, b):
    """Compare as dates when both sides look like dates, else as strings."""
    def as_date(raw):
        s = str(raw)
        d = resolve_date(s)
        if d is not None:
            return d
        try:
            return _dt.date.fromisoformat(s[:10])
        except ValueError:
            return None
    da, db = as_date(a), as_date(b)
    if da and db:
        return da, db
    return str(a), str(resolve_date(str(b)) or b)


def match_query(fm: dict, where: list, without=None) -> bool:
    for key in without or []:
        if fm_get(fm, key) is not None:
            return False
    for key, op, val in where:
        got = fm_get(fm, key)
        if got is None:
            return False        # a missing field never satisfies a comparison
        if op == "=":
            if str(got).strip().lower() != val.strip().lower():
                return False
            continue
        left, right = _coerce(got, val)
        if op == "<" and not left < right:
            return False
        if op == "<=" and not left <= right:
            return False
        if op == ">" and not left > right:
            return False
        if op == ">=" and not left >= right:
            return False
    return True


