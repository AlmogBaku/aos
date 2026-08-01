"""The finding sort order, preserved across the port.

The retired `aos-lint.mjs` sorted its findings with `String.prototype.localeCompare`, which
is ICU collation, not codepoint order: punctuation sorts before digits before letters, case
is a tiebreak rather than a 32-point jump, and `_` precedes `-`. Python's `sorted()` is
codepoint order, so porting the sort naively reordered the report on any tree with findings
— `MOD.md` moved from last to second, and every `capabilities/bad-cap/agents/…` row moved
past `capabilities/bad-cap/CAPABILITY.md`.

That is cosmetic in one sense and not in another: nothing parses this output, but a reviewer
comparing a pre- and post-port failure list would see dozens of moved lines and no way to
tell reordering from a changed verdict. So the order is reproduced instead of rationalized.

The table below is not hand-written — it is what `node -e "chars.sort((a,b) =>
a.localeCompare(b))"` returns for printable ASCII, which is the whole alphabet these paths
and codes use. A character outside it (no repo path has one) sorts after the table by
codepoint, which is the one case where this deliberately does not chase ICU: full Unicode
collation would mean shipping ICU to order a lint report.
"""

# Printable ASCII in ICU primary/secondary order, from node's own localeCompare.
_ICU_ASCII = (" _-,;:!?.'\"()[]{}@*/\\&#%`^+<=>|~$0123456789"
              "aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ")
_WEIGHT = {ch: i for i, ch in enumerate(_ICU_ASCII)}
_BEYOND = len(_ICU_ASCII)


def locale_key(text: str) -> tuple:
    """A sort key ordering strings the way JS `localeCompare` did."""
    return tuple(_WEIGHT.get(ch, _BEYOND + ord(ch)) for ch in text)
